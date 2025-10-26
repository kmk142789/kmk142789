"""Donation intake API with transparent logging and VC issuance."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class DonationReceipt:
    """Represents an inbound donation across multiple payment rails."""

    id: str
    donor: str
    amount: Decimal
    currency: str
    channel: str
    reference: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    credential: Mapping[str, Any] | None = None

    def to_public_dict(self) -> Dict[str, Any]:
        payload = {
            "id": self.id,
            "donor": self.donor,
            "amount": str(self.amount),
            "currency": self.currency,
            "channel": self.channel,
            "reference": self.reference,
            "timestamp": self.timestamp.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        }
        if self.metadata:
            payload["metadata"] = self.metadata
        if self.credential is not None:
            payload["credential"] = self.credential
        return payload


CredentialIssuerFn = Callable[..., Mapping[str, Any]]


class DonationIntakeAPI:
    """Collects donations and publishes public receipts."""

    def __init__(
        self,
        *,
        credential_issuer: CredentialIssuerFn | None = None,
        log_path: Path | None = None,
    ) -> None:
        self._issuer = credential_issuer
        self._log_path = log_path
        self._receipts: list[DonationReceipt] = []
        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            if not log_path.exists():
                log_path.write_text("")

    # ------------------------------------------------------------------
    # Recording helpers
    # ------------------------------------------------------------------
    def record_eth_donation(self, *, donor: str, amount_wei: int, tx_hash: str) -> DonationReceipt:
        amount_eth = Decimal(amount_wei) / Decimal(10**18)
        metadata = {"tx_hash": tx_hash, "network": "ethereum"}
        return self._record(
            donor=donor,
            amount=amount_eth,
            currency="ETH",
            channel="eth",
            reference=tx_hash,
            metadata=metadata,
        )

    def record_btc_donation(self, *, donor: str, amount_sats: int, txid: str) -> DonationReceipt:
        amount_btc = Decimal(amount_sats) / Decimal(10**8)
        metadata = {"txid": txid, "network": "bitcoin"}
        return self._record(
            donor=donor,
            amount=amount_btc,
            currency="BTC",
            channel="btc",
            reference=txid,
            metadata=metadata,
        )

    def record_fiat_donation(
        self,
        *,
        donor: str,
        amount: Decimal,
        currency: str,
        provider: str,
        receipt_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DonationReceipt:
        metadata = {"provider": provider, **(metadata or {})}
        return self._record(
            donor=donor,
            amount=amount,
            currency=currency.upper(),
            channel=provider.lower(),
            reference=receipt_id,
            metadata=metadata,
        )

    def _record(
        self,
        *,
        donor: str,
        amount: Decimal,
        currency: str,
        channel: str,
        reference: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DonationReceipt:
        receipt_id = f"donation-{uuid.uuid4()}"
        timestamp = _utc_now()
        receipt = DonationReceipt(
            id=receipt_id,
            donor=donor,
            amount=amount.quantize(Decimal("0.00000001")),
            currency=currency,
            channel=channel,
            reference=reference,
            timestamp=timestamp,
            metadata=metadata or {},
        )
        receipt.credential = self._issue_credential(receipt)
        self._receipts.append(receipt)
        self._append_log(receipt)
        return receipt

    # ------------------------------------------------------------------
    # Publication
    # ------------------------------------------------------------------
    def receipts(self) -> Sequence[DonationReceipt]:
        return tuple(self._receipts)

    def totals_by_currency(self) -> Dict[str, Decimal]:
        totals: Dict[str, Decimal] = {}
        for receipt in self._receipts:
            totals.setdefault(receipt.currency, Decimal("0"))
            totals[receipt.currency] += receipt.amount
        return totals

    def publish_dashboard(self) -> Dict[str, Any]:
        receipts = [receipt.to_public_dict() for receipt in self._receipts]
        totals = {currency: str(amount) for currency, amount in self.totals_by_currency().items()}
        return {
            "receipts": receipts,
            "totals": totals,
            "count": len(receipts),
        }

    def _issue_credential(self, receipt: DonationReceipt) -> Mapping[str, Any]:
        claims = {
            "donationId": receipt.id,
            "donor": receipt.donor,
            "amount": str(receipt.amount),
            "currency": receipt.currency,
            "channel": receipt.channel,
            "reference": receipt.reference,
        }
        if self._issuer is None:
            return {
                "id": receipt.id,
                "type": ["VerifiableCredential", "DonationReceipt"],
                "credentialSubject": claims,
                "issuer": "did:echo:simulated",
            }
        return self._issuer(
            subject_id=f"did:echo:donor:{receipt.donor}",
            claims=claims,
            types=("DonationReceipt",),
        )

    def _append_log(self, receipt: DonationReceipt) -> None:
        if self._log_path is None:
            return
        payload = json.dumps(receipt.to_public_dict(), sort_keys=True)
        with self._log_path.open("a", encoding="utf-8") as handle:
            handle.write(payload + "\n")

    def jsonl_feed(self) -> Iterable[str]:
        if self._log_path is None or not self._log_path.exists():
            return ()
        return tuple(self._log_path.read_text(encoding="utf-8").splitlines())
