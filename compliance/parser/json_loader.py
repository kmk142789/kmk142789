from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .models import Artifact, ArtifactType, Clause, Section, SourceLocation, StructuredPayload


def load_normalized(path: Path) -> Artifact:
    data = json.loads(path.read_text(encoding="utf-8"))
    artifact_type = ArtifactType(data["artifact_type"])
    sections: List[Section] = []
    for section_data in data.get("sections", []):
        clauses: List[Clause] = []
        for clause_data in section_data.get("clauses", []):
            structured: List[StructuredPayload] = []
            for payload in clause_data.get("structured_data", []):
                structured.append(
                    StructuredPayload(
                        language=payload.get("language", "text"),
                        payload=payload.get("payload"),
                    )
                )
            clauses.append(
                Clause(
                    id=clause_data["id"],
                    text=clause_data.get("text", ""),
                    tags=list(clause_data.get("tags", [])),
                    source=SourceLocation(
                        file=clause_data.get("source", {}).get("file", str(path)),
                        line_start=int(clause_data.get("source", {}).get("line_start", 1)),
                        line_end=int(clause_data.get("source", {}).get("line_end", 1)),
                    ),
                    heading_path=list(clause_data.get("heading_path", [])),
                    structured_data=structured,
                )
            )
        sections.append(Section(heading=section_data.get("heading", ""), clauses=clauses))

    artifact = Artifact(
        artifact_type=artifact_type,
        title=data.get("title", path.stem),
        source_path=path,
        sections=sections,
        metadata=dict(data.get("metadata", {})),
        roles={key: dict(value) for key, value in data.get("roles", {}).items()},
        committees=[dict(item) for item in data.get("committees", [])],
        trustees=[dict(item) for item in data.get("trustees", [])],
    )
    return artifact
