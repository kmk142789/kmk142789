"""High-level Atlas service."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional

from .adapters.sqlite import SQLiteAdapter
from .domain import AtlasSummary, Edge, Node
from .ingest import default_importers, run_importers
from .reporting import build_report, export_graph, write_report
from .storage.migrations import apply_migrations
from .storage.repository import AtlasRepository
from .storage.seed import load_seed
from .utils import ensure_directory
from .visualize import build_dot, build_svg, write_dot, write_svg


class AtlasService:
    """Coordinate storage, ingestion, and reporting."""

    def __init__(
        self,
        project_root: Path,
        adapter: Optional[SQLiteAdapter] = None,
        importers: Optional[Iterable] = None,
    ) -> None:
        self.project_root = project_root
        db_path = project_root / "data" / "atlas.db"
        ensure_directory(db_path.parent)
        self.adapter = adapter or SQLiteAdapter(db_path)
        self.repository = AtlasRepository(self.adapter)
        self._importers = importers

    def ensure_ready(self) -> None:
        apply_migrations(self.adapter)
        load_seed(self.repository)

    def sync(self) -> AtlasSummary:
        self.ensure_ready()
        importers = list(self._importers or default_importers(self.project_root))
        batch = run_importers(importers)
        for node in batch.nodes:
            self.repository.upsert_node(node)
        for edge in batch.edges:
            self.repository.upsert_edge(edge)
        summary = self.build_summary()
        graph_data = self.repository.export_graph()
        export_graph(self.project_root / "artifacts" / "atlas_graph.json", graph_data)
        write_report(self.project_root / "docs" / "ATLAS_REPORT.md", build_report(summary))
        nodes = self.repository.list_nodes()
        edges = self.repository.list_edges()
        write_dot(self.project_root / "artifacts" / "atlas_graph.dot", build_dot(nodes, edges))
        write_svg(self.project_root / "artifacts" / "atlas_graph.svg", build_svg(nodes, edges))
        return summary

    def build_summary(self) -> AtlasSummary:
        totals = self.repository.count_by_entity()
        relations = self.repository.count_by_relation()
        changes = self.repository.recent_changes(limit=10)
        highlight = self.repository.latest_highlight()
        if not highlight:
            highlight = self._default_highlight(totals, relations)
        return AtlasSummary(totals=totals, relations=relations, recent_changes=changes, highlights=highlight)

    def _default_highlight(self, totals: dict[str, int], relations: dict[str, int]) -> str:
        node_total = sum(totals.values())
        relation_total = sum(relations.values())
        return (
            f"Atlas tracks {node_total} entities with {relation_total} relationships. "
            "Use `echocli atlas show` to inspect a specific node."
        )

    def show_entity(self, name: str) -> tuple[Node, List[Edge]]:
        node = self.repository.find_node_by_name(name)
        if not node:
            raise LookupError(f"No atlas entity named '{name}'.")
        edges = self.repository.edges_for(node.identifier)
        return node, edges

    def append_highlight(self, text: str) -> None:
        self.repository.store_highlight(text)

    def list_nodes(self) -> List[Node]:
        return self.repository.list_nodes()

    def list_edges(self) -> List[Edge]:
        return self.repository.list_edges()

    def export_data(self) -> dict[str, object]:
        return dict(self.repository.export_graph())

    def atlas_path(self, *parts: str) -> Path:
        return self.project_root.joinpath(*parts)

    def change_log(self) -> List[dict[str, object]]:
        return list(self.repository.recent_changes())
