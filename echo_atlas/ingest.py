"""Ingestion orchestration for Echo Atlas."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from .importers.base import AtlasImporter, ImportBatch
from .importers.codeowners import CodeownersImporter
from .importers.control import ControlImporter
from .importers.docs import DocsImporter
from .importers.security import SecurityImporter


def default_importers(root: Path) -> List[AtlasImporter]:
    return [
        ControlImporter(root),
        SecurityImporter(root),
        CodeownersImporter(root),
        DocsImporter(root),
    ]


def run_importers(importers: Iterable[AtlasImporter]) -> ImportBatch:
    batch = ImportBatch()
    for importer in importers:
        batch.extend(importer.run())
    return batch
