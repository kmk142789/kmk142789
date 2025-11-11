from __future__ import annotations

from pathlib import Path

from echo_atlas.domain import Edge, EntityType, Node, RelationType
from echo_atlas.visualize import build_svg
from tests.golden import read_golden_text


def test_build_svg_matches_golden(tmp_path: Path) -> None:
    nodes = [
        Node(identifier="a", name="Alice", entity_type=EntityType.PERSON),
        Node(identifier="b", name="Echo", entity_type=EntityType.REPO),
    ]
    edges = [
        Edge(
            identifier="e",
            source="a",
            target="b",
            relation=RelationType.OWNS,
        )
    ]
    svg = build_svg(nodes, edges)
    assert svg == read_golden_text("atlas_graph_svg")
