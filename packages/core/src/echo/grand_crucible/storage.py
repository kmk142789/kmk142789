"""Persistence utilities for the grand crucible."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence

from .telemetry import TelemetrySnapshot


def ensure_directory(path: Path) -> None:
    """Ensure that the parent directory for the path exists."""

    path.parent.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str) -> None:
    ensure_directory(path)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: Mapping[str, object]) -> None:
    ensure_directory(path)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_storyline(path: Path, storyline: Sequence[str]) -> None:
    ensure_directory(path)
    path.write_text("\n".join(storyline), encoding="utf-8")


def write_telemetry(path: Path, snapshot: TelemetrySnapshot) -> None:
    write_json(path, snapshot.as_dict())


def write_composite_artifact(
    directory: Path,
    *,
    overview: str,
    heatmap: str,
    storyline: Sequence[str],
    telemetry: TelemetrySnapshot,
) -> None:
    """Persist a complete set of artifacts for a crucible run."""

    write_text(directory / "overview.txt", overview)
    write_text(directory / "heatmap.txt", heatmap)
    write_storyline(directory / "storyline.txt", storyline)
    write_telemetry(directory / "telemetry.json", telemetry)
