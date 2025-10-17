"""Importer registry for Echo Atlas."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from ..repository import AtlasRepository
from .base import AtlasImporter, ImporterResult
from .codeowners import CodeOwnersImporter
from .control import ControlImporter
from .docs import DocsImporter
from .security import SecurityImporter


def default_importers() -> List[AtlasImporter]:
    return [
        ControlImporter(),
        SecurityImporter(),
        CodeOwnersImporter(),
        DocsImporter(),
    ]


def run_importers(
    repository: AtlasRepository,
    root: Path,
    importers: Iterable[AtlasImporter] | None = None,
) -> List[ImporterResult]:
    results: List[ImporterResult] = []
    for importer in importers or default_importers():
        results.append(importer.run(repository, root))
    return results


__all__ = ["AtlasImporter", "ImporterResult", "default_importers", "run_importers"]
