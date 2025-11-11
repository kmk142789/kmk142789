from __future__ import annotations

from typing import List, Optional

from .base import ComplianceContext, Finding, make_alignment, make_tension
from ..parser.models import ArtifactType, Clause


_DEFENSIVE_IDS = [
    (ArtifactType.CHARTER, "CH-CUST-001"),
    (ArtifactType.TRUST, "TR-CUST-001"),
    (ArtifactType.DAO_OA, "DAO-CUST-001"),
]
_REPORTING_IDS = [
    (ArtifactType.CHARTER, "CH-CUST-002"),
    (ArtifactType.TRUST, "TR-DUTY-001"),
    (ArtifactType.DAO_OA, "DAO-CUST-002"),
]


def _get_clause(artifact: Optional[object], clause_id: str) -> Optional[Clause]:
    if not artifact:
        return None
    for clause in artifact.clauses():
        if clause.id == clause_id:
            return clause
    return None


def evaluate(context: ComplianceContext) -> List[Finding]:
    charter = context.artifacts.get(ArtifactType.CHARTER)
    trust = context.artifacts.get(ArtifactType.TRUST)
    dao = context.artifacts.get(ArtifactType.DAO_OA)
    findings = []

    defensive_clauses = []
    for art_type, clause_id in _DEFENSIVE_IDS:
        artifact = context.artifacts.get(art_type)
        clause = _get_clause(artifact, clause_id)
        if clause:
            defensive_clauses.append(clause)
    if defensive_clauses:
        findings.append(
            make_alignment(
                rule_id="CUST-ALIGN-BASE",
                title="Custody anchored in shared multi-signature controls",
                description="Charter, trust, and DAO documents all reference shared custody with UNA involvement.",
                references=defensive_clauses,
            )
        )

    emergency_refs: List[Clause] = []
    if trust:
        clause = _get_clause(trust, "TR-CUST-002")
        if clause:
            emergency_refs.append(clause)
    if dao:
        clause = _get_clause(dao, "DAO-AUTH-002")
        if clause:
            emergency_refs.append(clause)
    if emergency_refs:
        findings.append(
            make_tension(
                rule_id="CUST-EMERGENCY",
                title="Emergency custody introduces solo authority",
                description="Trust deed allows the Lead Trustee to freeze assets solo while DAO emergency pod assumes multi-sig execution, creating asymmetry in emergency custody.",
                references=emergency_refs,
                rationale="Lead Trustee freeze window lacks explicit UNA countersignature while DAO pod still requires 2-of-3 approvals.",
            )
        )

    reporting_clauses: List[Clause] = []
    for art_type, clause_id in _REPORTING_IDS:
        artifact = context.artifacts.get(art_type)
        clause = _get_clause(artifact, clause_id)
        if clause:
            reporting_clauses.append(clause)
    if reporting_clauses:
        findings.append(
            make_alignment(
                rule_id="CUST-REPORT",
                title="Custody reporting duties align",
                description="All artifacts include regular reporting obligations tied to custody operations.",
                references=reporting_clauses,
            )
        )

    return findings
