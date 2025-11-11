from __future__ import annotations

import re
from typing import List, Optional

from .base import ComplianceContext, Finding, make_alignment, make_tension
from ..parser.models import Artifact, ArtifactType, Clause


_AMENDMENT_IDS = ["CH-AMND-001", "TR-AMND-001", "DAO-AMND-001", "DAO-AMND-002"]
_TOKEN_PATTERN = re.compile(r"token", re.IGNORECASE)
_UNA_PATTERN = re.compile(r"UNA", re.IGNORECASE)


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
    amendment_clauses: List[Clause] = []

    for clause_id in _AMENDMENT_IDS:
        clause = _get_clause(charter, clause_id) or _get_clause(trust, clause_id) or _get_clause(dao, clause_id)
        if clause:
            amendment_clauses.append(clause)

    una_clauses = [clause for clause in amendment_clauses if _UNA_PATTERN.search(clause.text)]
    if una_clauses:
        findings.append(
            make_alignment(
                rule_id="AMND-UNA",
                title="UNA involvement required for amendments",
                description="Each artifact references UNA Guardian participation in amendment procedures.",
                references=una_clauses,
            )
        )

    token_clauses = [clause for clause in amendment_clauses if _TOKEN_PATTERN.search(clause.text)]
    non_token_clauses = [clause for clause in amendment_clauses if not _TOKEN_PATTERN.search(clause.text)]
    if token_clauses and non_token_clauses:
        findings.append(
            make_tension(
                rule_id="AMND-TOKEN-GAP",
                title="Token governance only appears in DAO agreement",
                description="DAO operating agreement requires token-holder approval, which is absent from charter and trust deed amendment language.",
                references=token_clauses + non_token_clauses,
                rationale="Token voting threshold is articulated in DAO OA but omitted elsewhere.",
            )
        )

    return findings
