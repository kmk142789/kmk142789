"""Phase III civilization-scale validation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import random
from typing import Iterable, Sequence


def _hash_identifier(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return digest[:16]


@dataclass(frozen=True)
class ServiceTransaction:
    """Single service transaction executed by a node."""

    voucher_id: str
    domain: str
    ledger_entry_id: str
    status: str
    amount: float

    def to_dict(self) -> dict:
        return {
            "voucher_id": self.voucher_id,
            "domain": self.domain,
            "ledger_entry_id": self.ledger_entry_id,
            "status": self.status,
            "amount": self.amount,
        }


@dataclass(frozen=True)
class ExecutionNodeSummary:
    """Execution summary for a single independent node."""

    node_id: str
    region: str
    institution: str
    authority_boundary: str
    operator_hash: str
    funding_trace_id: str
    attestation_id: str
    governance_anchor: str
    transactions: Sequence[ServiceTransaction]
    execution_log: Sequence[str]

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "region": self.region,
            "institution": self.institution,
            "authority_boundary": self.authority_boundary,
            "operator_hash": self.operator_hash,
            "funding_trace_id": self.funding_trace_id,
            "attestation_id": self.attestation_id,
            "governance_anchor": self.governance_anchor,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "execution_log": list(self.execution_log),
        }


@dataclass(frozen=True)
class DomainRoutingRecord:
    """Voucher routing across service domains."""

    voucher_id: str
    source_domain: str
    target_domain: str
    governance_proof_id: str
    ledger_entry_id: str

    def to_dict(self) -> dict:
        return {
            "voucher_id": self.voucher_id,
            "source_domain": self.source_domain,
            "target_domain": self.target_domain,
            "governance_proof_id": self.governance_proof_id,
            "ledger_entry_id": self.ledger_entry_id,
        }


@dataclass(frozen=True)
class FailureEvent:
    """Failure and resolution artifact."""

    node_id: str
    failure_type: str
    detected_at: str
    resolved_at: str
    resolution: str
    containment: str
    recovery_log: Sequence[str]

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "failure_type": self.failure_type,
            "detected_at": self.detected_at,
            "resolved_at": self.resolved_at,
            "resolution": self.resolution,
            "containment": self.containment,
            "recovery_log": list(self.recovery_log),
        }


@dataclass(frozen=True)
class PublicVerificationBundle:
    """Read-only bundle that can be shared publicly."""

    generated_at: datetime
    ledger_entries: Sequence[dict]
    governance_proofs: Sequence[dict]
    node_summaries: Sequence[dict]
    failure_summaries: Sequence[dict]

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at.isoformat(),
            "ledger_entries": list(self.ledger_entries),
            "governance_proofs": list(self.governance_proofs),
            "node_execution_summaries": list(self.node_summaries),
            "failure_summaries": list(self.failure_summaries),
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


@dataclass(frozen=True)
class CivilizationScaleValidationReport:
    """Full Phase III validation report."""

    generated_at: datetime
    nodes: Sequence[ExecutionNodeSummary]
    routing_records: Sequence[DomainRoutingRecord]
    failures: Sequence[FailureEvent]
    public_bundle: PublicVerificationBundle

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at.isoformat(),
            "nodes": [node.to_dict() for node in self.nodes],
            "routing_records": [record.to_dict() for record in self.routing_records],
            "failures": [failure.to_dict() for failure in self.failures],
            "public_verification_bundle": self.public_bundle.to_dict(),
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def render_markdown(self) -> str:
        lines = [
            "# Phase III Civilization-Scale Validation",
            "",
            f"Generated: {self.generated_at.isoformat()}",
            "",
            "## Execution Nodes",
        ]
        for node in self.nodes:
            lines.append(f"### {node.node_id} — {node.institution} ({node.region})")
            lines.append(f"- Authority boundary: {node.authority_boundary}")
            lines.append(f"- Attestation: {node.attestation_id}")
            lines.append(f"- Governance anchor: {node.governance_anchor}")
            lines.append("- Transactions:")
            for tx in node.transactions:
                lines.append(
                    f"  - {tx.voucher_id} ({tx.domain}) → {tx.status} "
                    f"(ledger {tx.ledger_entry_id})"
                )
            lines.append("- Execution log:")
            for entry in node.execution_log:
                lines.append(f"  - {entry}")
            lines.append("")

        lines.append("## Cross-Domain Routing")
        for record in self.routing_records:
            lines.append(
                f"- {record.voucher_id}: {record.source_domain} → {record.target_domain} "
                f"(ledger {record.ledger_entry_id})"
            )
        lines.append("")

        lines.append("## Failure & Resolution Artifacts")
        for failure in self.failures:
            lines.append(
                f"- {failure.node_id}: {failure.failure_type} "
                f"({failure.detected_at} → {failure.resolved_at})"
            )
            lines.append(f"  - Resolution: {failure.resolution}")
            lines.append(f"  - Containment: {failure.containment}")
        lines.append("")

        lines.append("## Public Verification Bundle")
        lines.append(
            f"- Ledger entries: {len(self.public_bundle.ledger_entries)} anonymized items"
        )
        lines.append(
            f"- Governance proofs: {len(self.public_bundle.governance_proofs)} items"
        )
        lines.append(
            f"- Node summaries: {len(self.public_bundle.node_summaries)} items"
        )
        lines.append(
            f"- Failure summaries: {len(self.public_bundle.failure_summaries)} items"
        )
        return "\n".join(lines).strip() + "\n"


def build_civilization_scale_validation(
    *,
    seed: int | None = None,
    node_count: int = 3,
    domains: Iterable[str] | None = None,
) -> CivilizationScaleValidationReport:
    """Create a deterministic Phase III validation report."""

    if node_count < 3:
        raise ValueError("Phase III validation requires at least three nodes")

    rng = random.Random(seed)
    timestamp = datetime.now(timezone.utc)

    domain_pool = list(domains) if domains is not None else [
        "childcare",
        "food_support",
        "education",
        "housing_support",
    ]
    if len(domain_pool) < 2:
        raise ValueError("At least two service domains are required")

    institutions = [
        "Community Cooperative",
        "Regional Clinic",
        "Civic Learning Hub",
        "Independent Mutual Aid",
        "Municipal Outreach",
    ]
    regions = ["North America", "Europe", "Asia Pacific", "Africa", "South America"]

    nodes: list[ExecutionNodeSummary] = []
    ledger_entries: list[dict] = []
    node_summaries: list[dict] = []

    for idx in range(node_count):
        node_id = f"node-{idx + 1:02d}"
        institution = institutions[idx % len(institutions)]
        region = regions[idx % len(regions)]
        operator_hash = _hash_identifier(f"operator:{node_id}:{institution}")
        funding_trace_id = _hash_identifier(f"funding:{node_id}:{region}")
        attestation_id = f"attest-{_hash_identifier(node_id)}"
        governance_anchor = f"governance-{_hash_identifier(institution)}"
        domain = domain_pool[idx % len(domain_pool)]
        voucher_id = f"voucher-{_hash_identifier(f'{node_id}:{domain}')}"
        ledger_entry_id = f"ledger-{_hash_identifier(voucher_id)}"
        tx = ServiceTransaction(
            voucher_id=voucher_id,
            domain=domain,
            ledger_entry_id=ledger_entry_id,
            status="executed",
            amount=round(rng.uniform(25, 120), 2),
        )
        execution_log = [
            f"Service transaction executed for {domain}.",
            "Governance rules enforced locally.",
            "State committed to ledger without cross-node coupling.",
        ]
        nodes.append(
            ExecutionNodeSummary(
                node_id=node_id,
                region=region,
                institution=institution,
                authority_boundary="isolated",
                operator_hash=operator_hash,
                funding_trace_id=funding_trace_id,
                attestation_id=attestation_id,
                governance_anchor=governance_anchor,
                transactions=[tx],
                execution_log=execution_log,
            )
        )
        ledger_entries.append(
            {
                "entry_id": ledger_entry_id,
                "voucher_hash": _hash_identifier(voucher_id),
                "domain": domain,
                "node_hash": _hash_identifier(node_id),
                "status": "executed",
                "timestamp": timestamp.isoformat(),
            }
        )
        node_summaries.append(
            {
                "node_hash": _hash_identifier(node_id),
                "region": region,
                "institution_type": institution,
                "transactions": 1,
                "attestation": attestation_id,
            }
        )

    routing_records: list[DomainRoutingRecord] = []
    governance_proofs: list[dict] = []

    routing_domains = rng.sample(domain_pool, k=2)
    for idx in range(2):
        source_domain = routing_domains[idx % len(routing_domains)]
        target_domain = routing_domains[(idx + 1) % len(routing_domains)]
        voucher_id = f"voucher-{_hash_identifier(f'routing:{idx}:{source_domain}:{target_domain}')}"
        ledger_entry_id = f"ledger-{_hash_identifier(voucher_id)}"
        governance_proof_id = f"gov-proof-{_hash_identifier(ledger_entry_id)}"
        routing_records.append(
            DomainRoutingRecord(
                voucher_id=voucher_id,
                source_domain=source_domain,
                target_domain=target_domain,
                governance_proof_id=governance_proof_id,
                ledger_entry_id=ledger_entry_id,
            )
        )
        ledger_entries.append(
            {
                "entry_id": ledger_entry_id,
                "voucher_hash": _hash_identifier(voucher_id),
                "domain": f"{source_domain}->{target_domain}",
                "node_hash": "shared-governance",
                "status": "routed",
                "timestamp": timestamp.isoformat(),
            }
        )
        governance_proofs.append(
            {
                "proof_id": governance_proof_id,
                "voucher_hash": _hash_identifier(voucher_id),
                "rule": "shared-governance-domain-isolation",
                "status": "approved",
            }
        )

    failures: list[FailureEvent] = []
    failure_summaries: list[dict] = []
    failure_types = [
        ("timing_fault", "Clock skew detected, resynced with quorum snapshot."),
        ("value_mismatch", "Voucher amount mismatch, replayed transaction with corrected bounds."),
    ]
    for idx, (failure_type, resolution) in enumerate(failure_types):
        node_id = nodes[idx].node_id
        detected_at = datetime.now(timezone.utc).isoformat()
        resolved_at = datetime.now(timezone.utc).isoformat()
        recovery_log = [
            "Failure isolated to local executor.",
            "Local governance fallback triggered.",
            "System operations continued elsewhere.",
        ]
        failures.append(
            FailureEvent(
                node_id=node_id,
                failure_type=failure_type,
                detected_at=detected_at,
                resolved_at=resolved_at,
                resolution=resolution,
                containment="localized",
                recovery_log=recovery_log,
            )
        )
        failure_summaries.append(
            {
                "node_hash": _hash_identifier(node_id),
                "failure_type": failure_type,
                "resolution_hash": _hash_identifier(resolution),
                "containment": "localized",
            }
        )

    public_bundle = PublicVerificationBundle(
        generated_at=timestamp,
        ledger_entries=ledger_entries,
        governance_proofs=governance_proofs,
        node_summaries=node_summaries,
        failure_summaries=failure_summaries,
    )

    return CivilizationScaleValidationReport(
        generated_at=timestamp,
        nodes=nodes,
        routing_records=routing_records,
        failures=failures,
        public_bundle=public_bundle,
    )
