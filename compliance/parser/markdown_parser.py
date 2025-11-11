from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .models import Artifact, ArtifactType, Clause, Section, SourceLocation, StructuredPayload


_HEADING_PATTERN = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<title>.+?)\s*$")
_METADATA_PATTERN = re.compile(r"^(?P<key>[A-Za-z0-9_-]+)\s*:\s*(?P<value>.+?)\s*$")
_TAG_PATTERN = re.compile(r"tags\s*:\s*(?P<value>.+)", re.IGNORECASE)
_ID_PATTERN = re.compile(r"clause\s*id\s*:\s*(?P<value>.+)", re.IGNORECASE)
_ROLES_HEADING = {"roles", "governance roles", "council roles"}
_COMMITTEE_HEADING = {"committees", "dao committees", "governance committees"}
_TRUSTEE_HEADING = {"trustees", "fiduciaries"}


@dataclass
class _ClauseBuilder:
    heading_path: List[str]
    start_line: int
    lines: List[str]
    structured: List[StructuredPayload]
    clause_id: Optional[str]
    tags: List[str]

    def build(self, source_file: Path, end_line: int) -> Optional[Clause]:
        content = "\n".join(line.rstrip() for line in self.lines).strip()
        if not content:
            return None
        text_lines = []
        for line in self.lines:
            if line.strip().lower().startswith("clause id:"):
                continue
            if line.strip().lower().startswith("tags:"):
                continue
            text_lines.append(line.rstrip())
        text = " ".join(segment.strip() for segment in "\n".join(text_lines).splitlines() if segment.strip())
        clause_id = self.clause_id or f"AUTO-{self.start_line}"
        return Clause(
            id=clause_id,
            text=text,
            tags=[tag.strip() for tag in self.tags if tag.strip()],
            source=SourceLocation(
                file=str(source_file),
                line_start=self.start_line,
                line_end=end_line,
            ),
            heading_path=list(self.heading_path),
            structured_data=list(self.structured),
        )


def _process_clause_line(builder: _ClauseBuilder, line: str) -> None:
    stripped = line.strip()
    if not stripped:
        return
    id_match = _ID_PATTERN.match(stripped)
    if id_match:
        builder.clause_id = id_match.group("value").strip()
        return
    tag_match = _TAG_PATTERN.match(stripped)
    if tag_match:
        builder.tags.extend(
            [tag.strip() for tag in tag_match.group("value").split(",") if tag.strip()]
        )
        return
    builder.lines.append(line)


def _finalize_clause(
    builder: Optional[_ClauseBuilder],
    clauses: List[Clause],
    source_file: Path,
    end_line: int,
) -> Optional[_ClauseBuilder]:
    if builder is not None:
        clause = builder.build(source_file, end_line)
        if clause:
            clauses.append(clause)
    return None


def parse_markdown(path: Path) -> Artifact:
    lines = path.read_text(encoding="utf-8").splitlines()
    metadata: Dict[str, object] = {}
    title: Optional[str] = None
    current_heading_path: List[str] = []
    sections: List[Section] = []
    current_section_clauses: List[Clause] = []
    clause_builder: Optional[_ClauseBuilder] = None
    roles: Dict[str, Dict[str, object]] = {}
    committees: List[Dict[str, object]] = []
    trustees: List[Dict[str, object]] = []

    def push_section():
        nonlocal current_section_clauses
        if len(current_heading_path) >= 2:
            sections.append(
                Section(heading=current_heading_path[-1], clauses=list(current_section_clauses))
            )
        current_section_clauses = []

    inside_code_block = False
    code_language: Optional[str] = None
    code_lines: List[str] = []

    for index, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip("\n")
        if not title:
            heading_match = _HEADING_PATTERN.match(line)
            if heading_match and heading_match.group("hashes") == "#":
                title = heading_match.group("title").strip()
                current_heading_path = [title]
                continue
        metadata_match = _METADATA_PATTERN.match(line)
        if metadata_match and not current_heading_path:
            key = metadata_match.group("key").strip().lower()
            value = metadata_match.group("value").strip()
            metadata[key] = value
            continue

        if line.strip().startswith("```"):
            if inside_code_block:
                payload = "\n".join(code_lines)
                if code_language and code_language.lower() == "json":
                    try:
                        parsed = json.loads(payload)
                    except json.JSONDecodeError:
                        parsed = payload
                else:
                    parsed = payload
                if clause_builder is not None:
                    clause_builder.structured.append(StructuredPayload(code_language or "text", parsed))
                inside_code_block = False
                code_language = None
                code_lines = []
            else:
                inside_code_block = True
                code_language = line.strip().lstrip("`").strip() or None
                code_lines = []
            continue
        if inside_code_block:
            code_lines.append(line)
            continue

        heading_match = _HEADING_PATTERN.match(line)
        if heading_match:
            level = len(heading_match.group("hashes"))
            heading_text = heading_match.group("title").strip()
            clause_builder = _finalize_clause(
                clause_builder, current_section_clauses, path, index - 1
            )
            if level == 2:
                push_section()
            current_heading_path = current_heading_path[: level - 1]
            current_heading_path.append(heading_text)
            continue

        if line.strip().startswith(('-', '*')):
            clause_builder = _finalize_clause(
                clause_builder, current_section_clauses, path, index - 1
            )
            clause_builder = _ClauseBuilder(
                heading_path=list(current_heading_path),
                start_line=index,
                lines=[],
                structured=[],
                clause_id=None,
                tags=[],
            )
            cleaned_line = line[1:].strip() if line.strip().startswith('-') else line.strip()
            _process_clause_line(clause_builder, cleaned_line)
            continue

        if clause_builder is None and line.strip():
            clause_builder = _ClauseBuilder(
                heading_path=list(current_heading_path),
                start_line=index,
                lines=[],
                structured=[],
                clause_id=None,
                tags=[],
            )
            _process_clause_line(clause_builder, line)
            continue

        if clause_builder is not None:
            lower_line = line.strip()
            if not lower_line and clause_builder:
                clause_builder = _finalize_clause(
                    clause_builder, current_section_clauses, path, index - 1
                )
                continue
            _process_clause_line(clause_builder, line)

        heading_lower = current_heading_path[-1].lower() if current_heading_path else ""
        if heading_lower in _ROLES_HEADING and ":" in line:
            name, desc = [part.strip() for part in line.split(":", 1)]
            roles[name] = {"description": desc}
        elif heading_lower in _COMMITTEE_HEADING and ":" in line:
            name, rest = [part.strip() for part in line.split(":", 1)]
            committees.append({"name": name, "mandate": rest})
        elif heading_lower in _TRUSTEE_HEADING and ":" in line:
            name, rest = [part.strip() for part in line.split(":", 1)]
            trustees.append({"name": name, "role": rest})

    clause_builder = _finalize_clause(clause_builder, current_section_clauses, path, len(lines))
    push_section()

    if not title:
        title = path.stem.replace("_", " ").title()

    artifact_type = metadata.get("artifact-type") or metadata.get("artifact_type")
    if not artifact_type:
        inferred = path.stem.lower()
        if "charter" in inferred:
            artifact_type = ArtifactType.CHARTER.value
        elif "trust" in inferred or "deed" in inferred:
            artifact_type = ArtifactType.TRUST.value
        else:
            artifact_type = ArtifactType.DAO_OA.value

    artifact = Artifact(
        artifact_type=ArtifactType(artifact_type),
        title=title,
        source_path=path,
        sections=sections,
        metadata=metadata,
        roles=roles,
        committees=committees,
        trustees=trustees,
    )
    return artifact
