from __future__ import annotations

from pathlib import Path
import json

from atlas.graph import ArtifactNode, Edge, FederationGraph
from atlas.reporting import generate_federated_colossus_report


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_generate_federated_colossus_report(tmp_path: Path) -> None:
    graph = FederationGraph(
        universes={
            "U1": {"sources": ["cosmos"], "artifact_count": 1, "edge_count": 1},
            "U2": {"sources": ["fractal"], "artifact_count": 1, "edge_count": 0},
        },
        artifacts=[
            ArtifactNode(
                node_id="U1::cycle-glyph",
                universe="U1",
                artifact_id="cycle-glyph",
                source="cosmos",
                metadata={"label": "Cycle 00001 glyph"},
                content="The COLOSSUS cycle_00001 glyph signature",
                dependencies=["U2::puzzle"],
                timestamp="2024-01-01T00:00:00Z",
            ),
            ArtifactNode(
                node_id="U2::puzzle",
                universe="U2",
                artifact_id="puzzle",
                source="fractal",
                metadata={"label": "Puzzle anchor"},
                content="Puzzle notes",
                dependencies=[],
                timestamp="2024-01-01T00:05:00Z",
            ),
        ],
        edges=[
            Edge(source="U1::cycle-glyph", target="U2::puzzle"),
        ],
    )
    graph_path = tmp_path / "atlas" / "global_graph.json"
    graph.save(graph_path)

    search_index_dir = tmp_path / "search"
    _write_json(
        search_index_dir / "index.json",
        {
            "entries": [
                {
                    "node_id": "U1::cycle-glyph",
                    "universe": "U1",
                    "artifact_id": "cycle-glyph",
                    "text": "Signal for COLOSSUS 00001 and cycle_00001 glyph signature",
                },
                {
                    "node_id": "U2::puzzle",
                    "universe": "U2",
                    "artifact_id": "puzzle",
                    "text": "Puzzle reference",
                },
            ]
        },
    )

    colossus_root = tmp_path / "colossus"
    cycle_dir = colossus_root / "cycle_00001"
    cycle_dir.mkdir(parents=True)
    _write_json(
        cycle_dir / "dataset_cycle_00001.json",
        {
            "cycle": 1,
            "timestamp": "2025-10-25T10:05:16Z",
            "glyph_signature": "∇≋⟁⟁::d648759b",
        },
    )
    _write_json(
        cycle_dir / "lineage_map_00001.json",
        {
            "anchors": [
                {
                    "type": "puzzle",
                    "ref": "puzzle_cycle_00001.md",
                    "relationships": ["dataset"],
                }
            ]
        },
    )

    second_cycle = colossus_root / "cycle_00002"
    second_cycle.mkdir()
    _write_json(
        second_cycle / "dataset_cycle_00002.json",
        {
            "cycle": 2,
            "timestamp": "2025-10-26T10:05:21Z",
            "glyph_signature": "∇∞≋∞::0bd660c0",
        },
    )

    harmonix_path = tmp_path / "harmonix_cycle1.echo.json"
    _write_json(
        harmonix_path,
        {
            "cycle": 1,
            "glyphs": "∇⊸≋∇",
            "mythocode": ["mutate_code :: ∇[CYCLE]⊸{JOY=0.99}"],
            "quantum_key": "∇1⊸0.99≋0011∇",
            "narrative": "Cycle 1 narrative",
        },
    )

    puzzle_root = tmp_path / "puzzles"
    puzzle_root.mkdir()
    puzzle_root.joinpath("puzzle_123.md").write_text(
        "\n".join(
            [
                "# Puzzle #123 Solution",
                "Body text",
                "```",
                "1EchoPuzzleAddress",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    puzzle_root.joinpath("puzzle_124.md").write_text(
        "\n".join(
            [
                "# Puzzle #124 Solution",
                "Another body",
                "```",
                "1EchoPuzzleAddress",
                "```",
            ]
        ),
        encoding="utf-8",
    )

    markdown_path = tmp_path / "report.md"
    json_path = tmp_path / "report.json"

    report = generate_federated_colossus_report(
        graph_path=graph_path,
        search_index_path=search_index_dir,
        colossus_root=colossus_root,
        puzzle_root=puzzle_root,
        harmonix_sources=[harmonix_path],
        markdown_path=markdown_path,
        json_path=json_path,
    )

    assert markdown_path.exists()
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "## Cycle Overview" in markdown
    assert "### Cycle 00001" in markdown
    assert "Harmonix Mythocode" in markdown
    assert "## Derived Address Catalog" in markdown

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["graph"]["artifacts"] == 2
    assert payload["search_index"]["entries"] == 2
    assert len(payload["cycles"]) == 2
    cycle_one = next(item for item in payload["cycles"] if item["cycle"] == 1)
    assert cycle_one["harmonix"]["glyphs"] == "∇⊸≋∇"
    assert cycle_one["search_hits"] == ["U1::cycle-glyph"]
    assert payload["addresses"] == [
        {"address": "1EchoPuzzleAddress", "count": 2, "puzzles": [123, 124]}
    ]

    assert report.graph_summary["universes"] == 2
    assert report.cycles[0].harmonix is not None

