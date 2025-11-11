from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Sequence

from ..parser.models import Artifact, ArtifactType, Clause, CrossLink


class FindingSeverity(str, Enum):
    CONTRADICTION = "contradiction"
    TENSION = "tension"
    ALIGNMENT = "alignment"


@dataclass
class Finding:
    rule_id: str
    title: str
    description: str
    severity: FindingSeverity
    references: List[Clause] = field(default_factory=list)
    rationale: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "references": [
                {
                    "clause": clause.id,
                    "artifact": clause.source.file,
                    "line_start": clause.source.line_start,
                    "line_end": clause.source.line_end,
                }
                for clause in self.references
            ],
            "rationale": self.rationale,
        }


@dataclass
class ComplianceContext:
    artifacts: Dict[ArtifactType, Artifact]
    crosslinks: List[CrossLink]

    def get(self, artifact_type: ArtifactType) -> Artifact:
        return self.artifacts[artifact_type]


def make_alignment(rule_id: str, title: str, description: str, references: Sequence[Clause]) -> Finding:
    return Finding(
        rule_id=rule_id,
        title=title,
        description=description,
        severity=FindingSeverity.ALIGNMENT,
        references=list(references),
    )


def make_tension(rule_id: str, title: str, description: str, references: Sequence[Clause], rationale: str) -> Finding:
    return Finding(
        rule_id=rule_id,
        title=title,
        description=description,
        severity=FindingSeverity.TENSION,
        references=list(references),
        rationale=rationale,
    )


def make_contradiction(rule_id: str, title: str, description: str, references: Sequence[Clause], rationale: str) -> Finding:
    return Finding(
        rule_id=rule_id,
        title=title,
        description=description,
        severity=FindingSeverity.CONTRADICTION,
        references=list(references),
        rationale=rationale,
    )
