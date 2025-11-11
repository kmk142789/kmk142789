from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

from .json_loader import load_normalized
from .markdown_parser import parse_markdown
from .models import Artifact, ArtifactType, CrossLink


def _load_crosslinks(path: Path) -> List[CrossLink]:
    data = json.loads(path.read_text(encoding="utf-8"))
    crosslinks: List[CrossLink] = []
    for entry in data:
        crosslinks.append(
            CrossLink(
                source_artifact=ArtifactType(entry["source"]["artifact"]),
                source_clause=entry["source"]["clause"],
                target_artifact=ArtifactType(entry["target"]["artifact"]),
                target_clause=entry["target"]["clause"],
                relationship=entry["relationship"],
                notes=entry.get("notes"),
            )
        )
    return crosslinks


def discover_artifacts(base_path: Path) -> Tuple[Dict[ArtifactType, Artifact], List[CrossLink]]:
    artifacts: Dict[ArtifactType, Artifact] = {}
    crosslinks: List[CrossLink] = []

    for path in sorted(base_path.glob("**/*")):
        if path.is_dir():
            continue
        if "samples" in path.parts:
            continue
        suffix = path.suffix.lower()
        if suffix not in {".md", ".json"}:
            continue
        if path.name.lower().endswith("crosslinks.json"):
            crosslinks.extend(_load_crosslinks(path))
            continue
        if suffix == ".md":
            artifact = parse_markdown(path)
        else:
            artifact = load_normalized(path)
        try:
            relative = path.relative_to(base_path)
        except ValueError:
            relative = path
        artifact.source_path = relative
        for clause in artifact.clauses():
            clause.source.file = str(relative)
        artifacts[artifact.artifact_type] = artifact

    return artifacts, crosslinks
