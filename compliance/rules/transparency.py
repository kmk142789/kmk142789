from __future__ import annotations

import re
from typing import List, Optional

from .base import ComplianceContext, Finding, make_alignment, make_tension
from ..parser.models import Artifact, ArtifactType, Clause


_ONCHAIN_IDS = ["CH-TRAN-002", "TR-TRAN-001", "DAO-TRAN-001"]
_AUDIT_IDS = ["CH-TRAN-001", "DAO-TRAN-002"]

_MONTHLY_PATTERN = re.compile(r"monthly", re.IGNORECASE)
_SEMI_ANNUAL_PATTERN = re.compile(r"semi-annual", re.IGNORECASE)
_ANNUAL_PATTERN = re.compile(r"annual", re.IGNORECASE)


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

    onchain_refs: List[Clause] = []
    for clause_id in _ONCHAIN_IDS:
        clause = _get_clause(charter, clause_id) or _get_clause(trust, clause_id) or _get_clause(dao, clause_id)
        if clause:
            onchain_refs.append(clause)
    if onchain_refs:
        findings.append(
            make_alignment(
                rule_id="TRAN-ONCHAIN",
                title="Monthly transparency loop",
                description="All artifacts require monthly disclosures tied to on-chain proofs or trustee attestations.",
                references=onchain_refs,
            )
        )

    audit_refs: List[Clause] = []
    for clause_id in _AUDIT_IDS:
        clause = _get_clause(charter, clause_id) or _get_clause(dao, clause_id)
        if clause:
            audit_refs.append(clause)
    if len(audit_refs) == 2:
        charter_clause, dao_clause = audit_refs
        charter_freq = _SEMI_ANNUAL_PATTERN.search(charter_clause.text)
        dao_freq = _ANNUAL_PATTERN.search(dao_clause.text)
        if charter_freq and dao_freq:
            findings.append(
                make_tension(
                    rule_id="TRAN-AUDIT-FREQUENCY",
                    title="Audit frequency mismatch",
                    description="Charter mandates semi-annual UNA audits while DAO OA references annual third-party audits.",
                    references=audit_refs,
                    rationale="Semi-annual vs annual cadence requires harmonization.",
                )
            )
        else:
            findings.append(
                make_alignment(
                    rule_id="TRAN-AUDIT",
                    title="Audit cadence aligned",
                    description="Audit cadence language is consistent across artifacts.",
                    references=audit_refs,
                )
            )

    return findings
