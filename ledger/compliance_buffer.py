"""Compliance buffer service for Echo Bank ledger integrations.

The service ingests ledger entries, classifies donation
transactions, issues verifiable compliance credentials, and
maintains a machine-auditable legal posture registry.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Dict, Optional


def _iso_now() -> str:
    """Return an ISO-8601 timestamp with UTC timezone."""

    return (
        datetime.now(tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


@dataclass(slots=True)
class ComplianceAnnotation:
    """Container for compliance metadata attached to a ledger entry."""

    payload: Dict[str, str]
    credential_path: Path


@dataclass(slots=True)
class ComplianceCredential:
    """Minimal verifiable credential describing donation compliance."""

    credential_id: str
    classification: str
    issued_at: str
    issuer: str
    jurisdiction: str
    policy_reference: str
    transaction_digest: str
    transaction_seq: int
    proof_bundle: str
    ots_receipt: Optional[str]

    def to_payload(self) -> Dict[str, Optional[str]]:
        return {
            "credential_id": self.credential_id,
            "classification": self.classification,
            "issued_at": self.issued_at,
            "issuer": self.issuer,
            "jurisdiction": self.jurisdiction,
            "policy_reference": self.policy_reference,
            "transaction_digest": self.transaction_digest,
            "transaction_seq": self.transaction_seq,
            "proof_bundle": self.proof_bundle,
            "ots_receipt": self.ots_receipt,
        }


class ComplianceBufferService:
    """Compliance buffer that classifies and records donation movements.

    Parameters
    ----------
    bank:
        Human-readable bank label.
    registry_path:
        Location of the legal posture registry JSONL file.
    credential_dir:
        Directory where credential artifacts are stored.
    issuer:
        Name of the issuing compliance authority.
    jurisdiction:
        Compliance jurisdiction descriptor.
    policy_reference:
        Identifier for the governing compliance policy.
    """

    def __init__(
        self,
        *,
        bank: str,
        registry_path: Path,
        credential_dir: Path,
        issuer: str,
        jurisdiction: str,
        policy_reference: str,
    ) -> None:
        self.bank = bank
        self.registry_path = registry_path
        self.credential_dir = credential_dir
        self.issuer = issuer
        self.jurisdiction = jurisdiction
        self.policy_reference = policy_reference
        self.credential_dir.mkdir(parents=True, exist_ok=True)
        registry_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def attach(
        self,
        *,
        entry: "LedgerEntry",
        digest: str,
        proof_path: Path,
        ots_receipt: Optional[str],
    ) -> ComplianceAnnotation:
        """Classify the transaction and emit compliance artifacts."""

        classification = self._classify(entry)
        credential = self._build_credential(
            entry=entry,
            digest=digest,
            proof_path=proof_path,
            ots_receipt=ots_receipt,
            classification=classification,
        )
        credential_path = self._write_credential(entry.seq, credential)
        self._append_registry_record(entry, credential, credential_path)
        payload = credential.to_payload() | {
            "registry_path": str(self.registry_path),
            "credential_path": str(credential_path),
        }
        return ComplianceAnnotation(payload=payload, credential_path=credential_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _classify(self, entry: "LedgerEntry") -> str:
        narrative = entry.narrative.lower()
        if entry.direction == "inflow" or "donation" in narrative:
            return "exempt-non-taxable-donation"
        return "general-funds"

    def _build_credential(
        self,
        *,
        entry: "LedgerEntry",
        digest: str,
        proof_path: Path,
        ots_receipt: Optional[str],
        classification: str,
    ) -> ComplianceCredential:
        issued_at = _iso_now()
        credential_id = f"{self.bank.lower().replace(' ', '-')}-compliance-{entry.seq:05d}"
        return ComplianceCredential(
            credential_id=credential_id,
            classification=classification,
            issued_at=issued_at,
            issuer=self.issuer,
            jurisdiction=self.jurisdiction,
            policy_reference=self.policy_reference,
            transaction_digest=digest,
            transaction_seq=entry.seq,
            proof_bundle=os.fspath(proof_path),
            ots_receipt=ots_receipt,
        )

    def _write_credential(
        self, seq: int, credential: ComplianceCredential
    ) -> Path:
        path = self.credential_dir / f"entry_{seq:05d}_credential.json"
        path.write_text(json.dumps(credential.to_payload(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def _append_registry_record(
        self,
        entry: "LedgerEntry",
        credential: ComplianceCredential,
        credential_path: Path,
    ) -> None:
        record = {
            "timestamp": _iso_now(),
            "bank": self.bank,
            "transaction_seq": entry.seq,
            "transaction_digest": credential.transaction_digest,
            "classification": credential.classification,
            "credential_path": os.fspath(credential_path),
            "registry": os.fspath(self.registry_path),
            "jurisdiction": self.jurisdiction,
            "issuer": self.issuer,
        }
        with self.registry_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


# Avoid circular imports at runtime by importing for type checking only.
try:  # pragma: no cover - optional typing helper
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:  # pragma: no cover
        from .little_footsteps_bank import LedgerEntry
except Exception:  # pragma: no cover - mypy friendly fallback
    pass
