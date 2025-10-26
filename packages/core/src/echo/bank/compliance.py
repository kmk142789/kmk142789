"""Compliance buffering utilities for Echo Bank.

The service keeps a rolling legal posture registry that records how each
movement through the Little Footsteps ledger has been classified.  This
layer is intentionally lightweight so it can run anywhere the sovereign
ledger is mirrored (local disk, Raspberry Pi guardians, encrypted VPSs).
"""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Protocol


def _iso_now() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class LedgerEntryProtocol(Protocol):  # pragma: no cover - structural typing helper
    seq: int
    direction: str
    amount: str
    asset: str
    timestamp: str
    narrative: str

    def digest(self) -> str:
        """Return the canonical digest representing the ledger payload."""


@dataclass(slots=True)
class ComplianceClaim:
    """Immutable compliance claim that anchors a ledger entry."""

    claim_id: str
    classification: str
    direction: str
    ledger_seq: int
    ledger_digest: str
    ledger_timestamp: str
    ledger_amount: str
    asset: str
    reference: str
    beneficiary: str
    issuer: str
    created_at: str
    notes: Optional[str] = None
    attachments: Optional[Dict[str, str]] = None

    def to_record(self) -> Dict[str, object]:
        record = asdict(self)
        if self.notes is None:
            record.pop("notes")
        if not self.attachments:
            record.pop("attachments")
        return record


class ComplianceBufferService:
    """Tag ledger entries with immutable compliance classifications."""

    def __init__(
        self,
        *,
        registry_path: Path | str = Path("state/legal/legal_posture_registry.jsonl"),
        issuer: str = "Echo Bank Compliance Buffer",
    ) -> None:
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.issuer = issuer
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def register_transaction(
        self,
        entry: LedgerEntryProtocol,
        *,
        reference: str,
        beneficiary: str,
        classification: str = "donation",
        notes: Optional[str] = None,
        attachments: Optional[Dict[str, str]] = None,
    ) -> ComplianceClaim:
        """Attach a compliance claim to ``entry`` and persist it."""

        claim = ComplianceClaim(
            claim_id=f"lf-{uuid.uuid4()}",
            classification=classification,
            direction=entry.direction,
            ledger_seq=entry.seq,
            ledger_digest=entry.digest(),
            ledger_timestamp=entry.timestamp,
            ledger_amount=entry.amount,
            asset=entry.asset,
            reference=reference,
            beneficiary=beneficiary,
            issuer=self.issuer,
            created_at=_iso_now(),
            notes=notes,
            attachments=attachments,
        )
        self._append_claim(claim)
        return claim

    def claims(self) -> list[ComplianceClaim]:
        """Return all persisted claims in load order."""

        if not self.registry_path.exists():
            return []
        entries: list[ComplianceClaim] = []
        for line in self.registry_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            entries.append(ComplianceClaim(**payload))
        return entries

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _append_claim(self, claim: ComplianceClaim) -> None:
        record = json.dumps(claim.to_record(), sort_keys=True)
        with self._lock:
            with self.registry_path.open("a", encoding="utf-8") as handle:
                handle.write(record + "\n")
