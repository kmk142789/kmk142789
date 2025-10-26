"""Automated disbursement module for Little Footsteps."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

from .donations import DonationIntakeAPI


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class DisbursementRecord:
    """Represents a donation-to-beneficiary payout."""

    id: str
    beneficiary: str
    amount: Decimal
    currency: str
    memo: str
    triggered_by: str
    timestamp: datetime
    source_receipts: tuple[str, ...]
    metadata: Dict[str, Any]

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "beneficiary": self.beneficiary,
            "amount": str(self.amount),
            "currency": self.currency,
            "memo": self.memo,
            "triggered_by": self.triggered_by,
            "timestamp": self.timestamp.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "source_receipts": list(self.source_receipts),
            "metadata": self.metadata,
        }


class BeneficiaryEngine:
    """Coordinates disbursements and publishes JSONL receipts."""

    def __init__(self, intake: DonationIntakeAPI, *, jsonl_path: Path) -> None:
        self.intake = intake
        self._jsonl_path = jsonl_path
        self._jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._jsonl_path.exists():
            self._jsonl_path.write_text("")
        self._records: list[DisbursementRecord] = []

    def available_balance(self, currency: str) -> Decimal:
        currency = currency.upper()
        donated = self.intake.totals_by_currency().get(currency, Decimal("0"))
        disbursed = sum(
            record.amount for record in self._records if record.currency.upper() == currency
        )
        return donated - disbursed

    def execute_payout(
        self,
        *,
        beneficiary: str,
        amount: Decimal,
        currency: str,
        memo: str,
        triggered_by: str,
        source_receipts: Optional[Sequence[str]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> DisbursementRecord:
        currency = currency.upper()
        balance = self.available_balance(currency)
        if balance < amount:
            raise ValueError("Insufficient funds for disbursement")

        record = DisbursementRecord(
            id=f"disbursement-{uuid.uuid4()}",
            beneficiary=beneficiary,
            amount=amount.quantize(Decimal("0.01")),
            currency=currency,
            memo=memo,
            triggered_by=triggered_by,
            timestamp=_utc_now(),
            source_receipts=tuple(source_receipts or ()),
            metadata=dict(metadata or {}),
        )
        self._records.append(record)
        self._append_log(record)
        return record

    def records(self) -> Sequence[DisbursementRecord]:
        return tuple(self._records)

    def jsonl_feed(self) -> Iterable[str]:
        return tuple(self._jsonl_path.read_text(encoding="utf-8").splitlines())

    def _append_log(self, record: DisbursementRecord) -> None:
        payload = json.dumps(record.to_public_dict(), sort_keys=True)
        with self._jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(payload + "\n")
