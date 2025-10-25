from __future__ import annotations

from pathlib import Path
import json

from atlas.dedupe import _build_search_index
from atlas.graph import ArtifactNode, FederationGraph
from atlas.search import search


def _harmonix_node(*, cycle: int, puzzle_id: int, address: str, content: str, node_suffix: str) -> ArtifactNode:
    return ArtifactNode(
        node_id=f"U99::harmonix-{node_suffix}",
        universe="U99",
        artifact_id=f"harmonix-{node_suffix}",
        source="harmonix",
        metadata={
            "type": "harmonix",
            "harmonix": {
                "cycle": cycle,
                "puzzle_id": puzzle_id,
                "address": address,
            },
            "label": f"Cycle {cycle}",
        },
        content=content,
        timestamp="2024-01-01T00:00:00Z",
    )


def test_search_index_contains_harmonix_fields(tmp_path: Path) -> None:
    graph = FederationGraph(
        universes={},
        artifacts=[
            _harmonix_node(
                cycle=7,
                puzzle_id=256,
                address="bc1qharmonix000256",
                content="Harmonix cycle 7 puzzle 256 signal",
                node_suffix="cycle7",
            )
        ],
        edges=[],
    )

    _build_search_index(graph, tmp_path)
    payload = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))
    assert payload["entries"][0]["cycle"] == 7
    assert payload["entries"][0]["puzzle_id"] == 256
    assert payload["entries"][0]["address"] == "bc1qharmonix000256"


def test_search_filters_by_cycle_puzzle_and_address(tmp_path: Path) -> None:
    graph = FederationGraph(
        universes={},
        artifacts=[
            _harmonix_node(
                cycle=7,
                puzzle_id=256,
                address="bc1qharmonix000256",
                content="Harmonix cycle 7 puzzle 256 signal",
                node_suffix="cycle7",
            ),
            _harmonix_node(
                cycle=8,
                puzzle_id=512,
                address="bc1qharmonix000512",
                content="Harmonix cycle 8 puzzle 512 signal",
                node_suffix="cycle8",
            ),
        ],
        edges=[],
    )

    _build_search_index(graph, tmp_path)

    results = search(tmp_path, "harmonix", limit=5, cycle=7)
    assert [entry["puzzle_id"] for entry in results] == [256]

    results = search(tmp_path, "harmonix", limit=5, puzzle=512)
    assert [entry["cycle"] for entry in results] == [8]

    results = search(tmp_path, "signal", limit=5, address="bc1qharmonix000256")
    assert [entry["puzzle_id"] for entry in results] == [256]

    assert not search(tmp_path, "harmonix", limit=5, cycle=9)
