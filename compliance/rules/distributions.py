from __future__ import annotations

import re
from typing import Dict, List, Optional

from .base import (
    ComplianceContext,
    Finding,
    FindingSeverity,
    make_alignment,
    make_contradiction,
    make_tension,
)
from ..parser.models import Artifact, ArtifactType, Clause


_DISCRETIONARY_IDS = ["CH-FUND-001", "TR-DIST-002", "DAO-DIST-001"]
_RESTRICTED_IDS = ["TR-DIST-001", "DAO-DIST-002"]


def _get_clause(artifact: Optional[Artifact], clause_id: str) -> Optional[Clause]:
    if not artifact:
        return None
    for clause in artifact.clauses():
        if clause.id == clause_id:
            return clause
    return None


def _extract_percentage(clause: Clause) -> Optional[int]:
    match = re.search(r"(\d+)%", clause.text)
    if match:
        return int(match.group(1))
    return None


def evaluate(context: ComplianceContext) -> List[Finding]:
    charter = context.artifacts.get(ArtifactType.CHARTER)
    trust = context.artifacts.get(ArtifactType.TRUST)
    dao = context.artifacts.get(ArtifactType.DAO_OA)

    findings: List[Finding] = []

    discretionary: Dict[str, int] = {}
    discretionary_refs: List[Clause] = []
    for clause_id in _DISCRETIONARY_IDS:
        clause = _get_clause(charter, clause_id) or _get_clause(trust, clause_id) or _get_clause(dao, clause_id)
        if clause:
            pct = _extract_percentage(clause)
            if pct is not None:
                discretionary[clause.id] = pct
                discretionary_refs.append(clause)
    if len(discretionary) >= 2:
        min_pct = min(discretionary.values())
        max_pct = max(discretionary.values())
        if max_pct > min_pct:
            findings.append(
                make_contradiction(
                    rule_id="DIST-DISCRETIONARY",
                    title="Inconsistent discretionary spend ceilings",
                    description="Artifacts disagree on the maximum discretionary treasury percentage.",
                    references=discretionary_refs,
                    rationale=f"Observed discretionary ceilings range from {min_pct}% to {max_pct}%.",
                )
            )
    if discretionary_refs and not any(f.severity == FindingSeverity.CONTRADICTION for f in findings):
        findings.append(
            make_alignment(
                rule_id="DIST-DISCRETIONARY-ALIGN",
                title="Discretionary caps harmonized",
                description="All artifacts align on discretionary caps.",
                references=discretionary_refs,
            )
        )

    restricted_refs: List[Clause] = []
    for clause_id in _RESTRICTED_IDS:
        clause = _get_clause(trust, clause_id) or _get_clause(dao, clause_id)
        if clause:
            restricted_refs.append(clause)
    if restricted_refs:
        findings.append(
            make_alignment(
                rule_id="DIST-RESTRICTED",
                title="Restricted fund controls documented",
                description="Trust deed and DAO agreement both demand UNA review for restricted grants.",
                references=restricted_refs,
            )
        )

    if trust and dao:
        trust_clause = _get_clause(trust, "TR-DIST-002")
        dao_clause = _get_clause(dao, "DAO-DIST-001")
        if trust_clause and dao_clause:
            trust_pct = _extract_percentage(trust_clause)
            dao_pct = _extract_percentage(dao_clause)
            if trust_pct and dao_pct and dao_pct > trust_pct:
                findings.append(
                    make_tension(
                        rule_id="DIST-DAO-OVERRUN",
                        title="DAO discretionary window exceeds trustee authorization",
                        description="DAO experimentation vault cap is larger than what the trust deed permits.",
                        references=[trust_clause, dao_clause],
                        rationale=f"Trust deed cap {trust_pct}% vs DAO experimentation cap {dao_pct}%.",
                    )
                )
    return findings
