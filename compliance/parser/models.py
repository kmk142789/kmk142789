from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Iterable, List, Optional


class ArtifactType(str, Enum):
    CHARTER = "charter"
    TRUST = "trust"
    DAO_OA = "dao_oa"
    CROSSLINKS = "crosslinks"


@dataclass
class SourceLocation:
    file: str
    line_start: int
    line_end: int

    def to_dict(self) -> Dict[str, object]:
        return {
            "file": self.file,
            "line_start": self.line_start,
            "line_end": self.line_end,
        }


@dataclass
class StructuredPayload:
    language: str
    payload: object

    def to_dict(self) -> Dict[str, object]:
        return {"language": self.language, "payload": self.payload}


@dataclass
class Clause:
    id: str
    text: str
    tags: List[str]
    source: SourceLocation
    heading_path: List[str] = field(default_factory=list)
    structured_data: List[StructuredPayload] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "text": self.text,
            "tags": list(self.tags),
            "source": self.source.to_dict(),
            "heading_path": list(self.heading_path),
            "structured_data": [payload.to_dict() for payload in self.structured_data],
        }


@dataclass
class Section:
    heading: str
    clauses: List[Clause]

    def to_dict(self) -> Dict[str, object]:
        return {
            "heading": self.heading,
            "clauses": [clause.to_dict() for clause in self.clauses],
        }


@dataclass
class Artifact:
    artifact_type: ArtifactType
    title: str
    source_path: Path
    sections: List[Section]
    metadata: Dict[str, object] = field(default_factory=dict)
    roles: Dict[str, Dict[str, object]] = field(default_factory=dict)
    committees: List[Dict[str, object]] = field(default_factory=list)
    trustees: List[Dict[str, object]] = field(default_factory=list)

    def clauses_with_tag(self, tag: str) -> Iterable[Clause]:
        for section in self.sections:
            for clause in section.clauses:
                if tag in clause.tags:
                    yield clause

    def clauses(self) -> Iterable[Clause]:
        for section in self.sections:
            yield from section.clauses

    def to_dict(self) -> Dict[str, object]:
        data: Dict[str, object] = {
            "artifact_type": self.artifact_type.value,
            "title": self.title,
            "source_path": str(self.source_path),
            "metadata": dict(self.metadata),
            "sections": [section.to_dict() for section in self.sections],
        }
        if self.roles:
            data["roles"] = {key: dict(value) for key, value in self.roles.items()}
        if self.committees:
            data["committees"] = [dict(item) for item in self.committees]
        if self.trustees:
            data["trustees"] = [dict(item) for item in self.trustees]
        return data


@dataclass
class CrossLink:
    source_artifact: ArtifactType
    source_clause: str
    target_artifact: ArtifactType
    target_clause: str
    relationship: str
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        data = {
            "source": {
                "artifact": self.source_artifact.value,
                "clause": self.source_clause,
            },
            "target": {
                "artifact": self.target_artifact.value,
                "clause": self.target_clause,
            },
            "relationship": self.relationship,
        }
        if self.notes:
            data["notes"] = self.notes
        return data
