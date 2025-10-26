"""Public transparency portal scaffolding for transparency.bank."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from .beneficiary import BeneficiaryEngine
from .compliance import ComplianceShield
from .donations import DonationIntakeAPI
from .governance import GovernanceRegistry


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class TransparencyPortal:
    """Aggregates governance, inflow, outflow, and telemetry data."""

    def __init__(
        self,
        *,
        governance: GovernanceRegistry,
        intake: DonationIntakeAPI,
        beneficiary: BeneficiaryEngine,
        compliance: ComplianceShield,
    ) -> None:
        self.governance = governance
        self.intake = intake
        self.beneficiary = beneficiary
        self.compliance = compliance

    def snapshot(self) -> Dict[str, Any]:
        governance_payload = {
            "entity": self.governance.entity_name,
            "latest_version": self.governance.latest().version,
            "history": [version.as_record() for version in self.governance.history()],
        }
        inflows = self.intake.publish_dashboard()
        outflows = [record.to_public_dict() for record in self.beneficiary.records()]
        compliance_entries = [entry.to_public_dict() for entry in self.compliance.legal_defense_stream()]
        telemetry = {
            "timestamp": _utc_now_iso(),
            "donation_count": len(inflows["receipts"]),
            "disbursement_count": len(outflows),
            "latest_charter_version": governance_payload["latest_version"],
        }
        return {
            "entity": self.governance.entity_name,
            "governance": governance_payload,
            "inflows": inflows,
            "outflows": outflows,
            "compliance": compliance_entries,
            "telemetry": telemetry,
        }
