"""Compliance shield for donation-only operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, Mapping, Sequence

from .beneficiary import DisbursementRecord
from .donations import DonationReceipt


@dataclass
class ComplianceEntry:
    """Single entry in the legal defense ledger."""

    reference_id: str
    category: str
    irs_code: str
    rationale: str
    timestamp: datetime

    def to_public_dict(self) -> Dict[str, str]:
        return {
            "reference_id": self.reference_id,
            "category": self.category,
            "irs_code": self.irs_code,
            "rationale": self.rationale,
            "timestamp": self.timestamp.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        }


class ComplianceShield:
    """Maps donations to exemption logic and emits a legal defense ledger."""

    def __init__(self, *, entity_name: str, exemption_code: str = "501(c)(3)") -> None:
        self.entity_name = entity_name
        self.exemption_code = exemption_code
        self._entries: list[ComplianceEntry] = []

    def record_donation(self, receipt: DonationReceipt) -> ComplianceEntry:
        rationale = (
            f"Donation from {receipt.donor} routed via {receipt.channel.upper()} "
            f"supports charitable programming for Little Footsteps under IRS {self.exemption_code}."
        )
        entry = ComplianceEntry(
            reference_id=receipt.id,
            category="donation",
            irs_code=self.exemption_code,
            rationale=rationale,
            timestamp=datetime.now(timezone.utc),
        )
        self._entries.append(entry)
        return entry

    def record_disbursement(self, record: DisbursementRecord) -> ComplianceEntry:
        rationale = (
            f"Disbursement {record.id} delivers {record.currency} resources to {record.beneficiary} "
            "as a direct charitable expense, preserving donor intent."
        )
        entry = ComplianceEntry(
            reference_id=record.id,
            category="disbursement",
            irs_code=self.exemption_code,
            rationale=rationale,
            timestamp=datetime.now(timezone.utc),
        )
        self._entries.append(entry)
        return entry

    def legal_defense_stream(self) -> Sequence[ComplianceEntry]:
        return tuple(self._entries)

    def publish(self) -> Dict[str, Sequence[Dict[str, str]]]:
        return {"entries": tuple(entry.to_public_dict() for entry in self._entries)}
