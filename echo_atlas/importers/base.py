"""Importer interfaces for Echo Atlas."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ..repository import AtlasRepository


@dataclass(slots=True)
class ImporterResult:
    """Summary of importer execution."""

    name: str
    nodes: int
    edges: int


class AtlasImporter:
    """Base class for document importers."""

    name = "base"

    def run(self, repository: AtlasRepository, root: Path) -> ImporterResult:
        raise NotImplementedError

    @staticmethod
    def read_lines(path: Path) -> Iterable[str]:
        return path.read_text(encoding="utf-8").splitlines()
