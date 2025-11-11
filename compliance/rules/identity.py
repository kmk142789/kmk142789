from __future__ import annotations

from typing import List, Optional

from .base import ComplianceContext, Finding, make_alignment, make_tension
from ..parser.models import Artifact, ArtifactType, Clause


_ISSUANCE_IDS = ["CH-ID-001", "TR-ID-001", "DAO-ID-001"]
_SUSPENSION_IDS = ["CH-ID-002", "DAO-ID-002"]


def _get_clause(artifact: Optional[Artifact], clause_id: str) -> Optional[Clause]:
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

    findings: List[Finding] = []

    issuance_refs: List[Clause] = []
    for clause_id in _ISSUANCE_IDS:
        clause = _get_clause(charter, clause_id) or _get_clause(trust, clause_id) or _get_clause(dao, clause_id)
        if clause:
            issuance_refs.append(clause)
    if issuance_refs:
        findings.append(
            make_alignment(
                rule_id="ID-ISSUANCE",
                title="Identity issuance requires dual controls",
                description="Charter, trust, and DAO artifacts all point to Identity Circle plus Guardian participation.",
                references=issuance_refs,
            )
        )

    suspension_refs: List[Clause] = []
    for clause_id in _SUSPENSION_IDS:
        clause = _get_clause(charter, clause_id) or _get_clause(dao, clause_id)
        if clause:
            suspension_refs.append(clause)
    if len(suspension_refs) == 2:
        findings.append(
            make_tension(
                rule_id="ID-SUSPENSION",
                title="Emergency suspension actor differs from charter",
                description="DAO emergency pod may suspend credentials for 48 hours even though the charter reserves suspension to the Guardian UNA Board.",
                references=suspension_refs,
                rationale="Emergency Response Pod suspension power introduces a temporary divergence from UNA-led revocation.",
            )
        )

    return findings
