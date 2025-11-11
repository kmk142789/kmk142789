from __future__ import annotations

from typing import Dict, List, Tuple

from .base import (
    ComplianceContext,
    make_alignment,
    make_contradiction,
    make_tension,
)
from ..parser.models import ArtifactType, Clause


def _extract_actions(clause: Clause) -> List[Dict[str, str]]:
    actions: List[Dict[str, str]] = []
    for payload in clause.structured_data:
        data = payload.payload
        if isinstance(data, dict) and data.get("action"):
            record = {key: str(value) for key, value in data.items() if isinstance(value, (str, int))}
            for key, value in data.items():
                if isinstance(value, list):
                    record[key] = ", ".join(str(item) for item in value)
            actions.append(record)
    return actions


def evaluate(context: ComplianceContext) -> List[Finding]:
    findings: List[Finding] = []
    action_registry: Dict[str, List[Tuple[Clause, Dict[str, str]]]] = {}

    for artifact_type in [ArtifactType.CHARTER, ArtifactType.TRUST, ArtifactType.DAO_OA]:
        artifact = context.artifacts.get(artifact_type)
        if not artifact:
            continue
        for clause in artifact.clauses():
            for action in _extract_actions(clause):
                action_registry.setdefault(action["action"], []).append((clause, action))

    for action, records in action_registry.items():
        thresholds = {record.get("threshold") for _, record in records if record.get("threshold")}
        if len(thresholds) > 1:
            findings.append(
                make_contradiction(
                    rule_id=f"AUTH-{action.upper()}",
                    title=f"Conflicting authority thresholds for {action}",
                    description="Artifacts define inconsistent quorum thresholds for the same action.",
                    references=[clause for clause, _ in records],
                    rationale=f"Threshold values observed: {', '.join(sorted(thresholds))}",
                )
            )
            continue
        requires_sets = [
            set(record.get("requires", "").split(", "))
            for _, record in records
            if record.get("requires")
        ]
        if requires_sets:
            first = requires_sets[0]
            if any(req != first for req in requires_sets[1:]):
                findings.append(
                    make_tension(
                        rule_id=f"AUTH-REQ-{action.upper()}",
                        title=f"Mismatched secondary approvals for {action}",
                        description="Artifacts disagree on secondary approval requirements.",
                        references=[clause for clause, _ in records],
                        rationale="; ".join(
                            f"{clause.id} requires {info.get('requires')}"
                            for clause, info in records
                            if info.get("requires")
                        ),
                    )
                )
                continue
        solo_authorities = [
            record for _, record in records if record.get("threshold") in {"1-of-1", "solo"}
        ]
        multi_sigs = [record for _, record in records if record.get("threshold") not in {"1-of-1", "solo", None}]
        if solo_authorities and multi_sigs:
            findings.append(
                make_tension(
                    rule_id=f"AUTH-SOLO-{action.upper()}",
                    title=f"Solo override present for {action}",
                    description="At least one artifact introduces a solo execution path while others require multi-signature thresholds.",
                    references=[clause for clause, _ in records],
                    rationale="Solo authority detected alongside multi-sig requirements.",
                )
            )
        else:
            findings.append(
                make_alignment(
                    rule_id=f"AUTH-ALIGN-{action.upper()}",
                    title=f"Aligned authority for {action}",
                    description="All artifacts share the same quorum expectations for this action.",
                    references=[clause for clause, _ in records],
                )
            )
    return findings
