"""Base importer definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from ..domain import Edge, Node


@dataclass(slots=True)
class ImportBatch:
    nodes: List[Node] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)

    def extend(self, other: "ImportBatch") -> None:
        self.nodes.extend(other.nodes)
        self.edges.extend(other.edges)


class AtlasImporter:
    """Abstract importer base class."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def run(self) -> ImportBatch:
        raise NotImplementedError
