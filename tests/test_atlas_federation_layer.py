from __future__ import annotations

from pathlib import Path
import json

from atlas.dedupe import DedupeIndex, main as dedupe_cli
from atlas.federation import build_global_graph
from atlas.merge import main as merge_cli
from atlas.resolver import merge_universes
from atlas.search import search


def _write_payload(path: Path, universe: str, artifacts: list[dict], generated_at: str | None = None) -> None:
    payload = {"universe": universe, "artifacts": artifacts}
    if generated_at:
        payload["generated_at"] = generated_at
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_atlas_federation_end_to_end(tmp_path: Path) -> None:
    cosmos_dir = tmp_path / "cosmos"
    fractal_dir = tmp_path / "fractal"
    harmonix_dir = tmp_path / "harmonix"
    cosmos_dir.mkdir()
    fractal_dir.mkdir()
    harmonix_dir.mkdir()

    _write_payload(
        cosmos_dir / "u42.json",
        "U42",
        [
            {
                "id": "root",
                "content": "Merkle root 88KEY",
                "metadata": {"type": "ledger", "label": "Prime Root"},
                "dependencies": ["ledger", "U73::root"],
                "timestamp": "2024-05-01T00:00:00",
            },
            {
                "id": "ledger",
                "content": "Ledger shard 42",
                "metadata": {"type": "ledger", "height": 42},
                "dependencies": ["U88:mirror"],
                "timestamp": "2024-05-01T00:05:00",
            },
        ],
        generated_at="2024-05-01T00:10:00",
    )

    _write_payload(
        cosmos_dir / "u73.json",
        "U73",
        [
            {
                "id": "root",
                "content": "Merkle root 88KEY",
                "metadata": {"type": "ledger", "label": "Prime Root"},
                "dependencies": [],
                "timestamp": "2024-05-02T12:00:00",
            }
        ],
        generated_at="2024-05-02T12:01:00",
    )

    _write_payload(
        fractal_dir / "u88.json",
        "U88",
        [
            {
                "id": "mirror",
                "content": "Fractal mirror",
                "metadata": {"type": "fractal", "label": "Mirror"},
                "dependencies": [],
                "timestamp": "2024-05-01T00:02:00",
            }
        ],
    )

    _write_payload(
        cosmos_dir / "chronos.json",
        "Chronos",
        [
            {
                "id": "anchor-001",
                "content": "Chronos anchor",
                "metadata": {"type": "anchor", "label": "C-001"},
                "dependencies": [],
                "timestamp": "2024-05-03T00:00:00",
            }
        ],
    )

    _write_payload(
        fractal_dir / "puzzles.json",
        "Puzzles",
        [
            {
                "id": "puzzle-251",
                "content": "Recovered puzzle",
                "metadata": {"type": "puzzle", "label": "251"},
                "dependencies": [],
                "timestamp": "2024-05-04T00:00:00",
            }
        ],
    )

    harmonix_snapshot = {
        "universe": "Harmonix",
        "cycles": [
            {
                "cycle": 1,
                "summary": "Cycle 1 summary",
                "timestamp": "2024-05-05T00:00:00",
                "metadata": {
                    "cycle_lineage": ["cycle-0000"],
                    "puzzle_references": [
                        {"universe": "Puzzles", "artifact_id": "puzzle-251"},
                        "Puzzles::puzzle-252",
                    ],
                    "chronos_anchors": [
                        {"universe": "Chronos", "artifact_id": "anchor-001"}
                    ],
                },
            },
            {
                "cycle": 2,
                "summary": "Cycle 2 summary",
                "timestamp": "2024-05-06T00:00:00",
                "dependencies": ["Chronos:anchor-001"],
                "metadata": {
                    "cycle_lineage": [{"cycle": 1}],
                },
            },
        ],
    }
    snapshot_path = harmonix_dir / "snapshots" / "cycles.json"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps(harmonix_snapshot, indent=2), encoding="utf-8")

    graph = build_global_graph(cosmos_dir, fractal_dir, harmonix_dir)
    assert set(graph.universes) == {"U42", "U73", "U88", "Chronos", "Puzzles", "Harmonix"}
    assert graph.universes["U42"]["artifact_count"] == 2
    assert graph.universes["Harmonix"]["artifact_count"] == 2
    assert any(edge.source == "U42::root" and edge.target == "U73::root" for edge in graph.edges)
    assert any(node.node_id == "U73::root" for node in graph.artifacts)
    harmonix_cycle_one = next(node for node in graph.artifacts if node.node_id == "Harmonix::cycle-0001")
    assert harmonix_cycle_one.timestamp == "2024-05-05T00:00:00"
    assert "Harmonix::cycle-0000" in harmonix_cycle_one.dependencies
    assert "Chronos::anchor-001" in harmonix_cycle_one.dependencies
    assert harmonix_cycle_one.metadata["normalized_cycle_lineage"] == ["Harmonix::cycle-0000"]
    assert harmonix_cycle_one.metadata["normalized_puzzle_references"][0] == "Puzzles::puzzle-251"
    assert harmonix_cycle_one.metadata["normalized_chronos_anchors"] == ["Chronos::anchor-001"]
    harmonix_cycle_two = next(node for node in graph.artifacts if node.node_id == "Harmonix::cycle-0002")
    assert "Harmonix::cycle-0001" in harmonix_cycle_two.dependencies
    assert "Chronos::anchor-001" in harmonix_cycle_two.dependencies
    assert harmonix_cycle_two.metadata["normalized_cycle_lineage"] == ["Harmonix::cycle-0001"]

    atlas_dir = tmp_path / "atlas"
    graph_path = atlas_dir / "global_graph.json"
    graph.save(graph_path)

    dedupe_out = atlas_dir / "dedupe_index.json"
    search_index_dir = atlas_dir / "federated_search_index"
    dedupe_cli([
        "--graph",
        str(graph_path),
        "--out",
        str(dedupe_out),
        "--search-index",
        str(search_index_dir),
    ])

    dedupe_index = DedupeIndex.load(dedupe_out)
    signatures = {tuple(record.universes) for record in dedupe_index.records if len(record.nodes) > 1}
    assert ("U42", "U73") in signatures or ("U73", "U42") in signatures

    results = search(search_index_dir, "Merkle root 88KEY", limit=5)
    assert results and results[0]["node_id"].startswith("U")

    merged = merge_universes(graph, ["U42", "U73"], policy="latest-wins")
    assert merged["artifacts"]["root"]["universe"] == "U73"

    merge_out = atlas_dir / "merged_state"
    exit_code = merge_cli(
        [
            "--graph",
            str(graph_path),
            "--universe",
            "U42",
            "U73",
            "--policy",
            "latest-wins",
            "--out",
            str(merge_out),
        ]
    )
    assert exit_code == 0
    merged_path = merge_out / "merged_state.json"
    assert merged_path.exists()
    payload = json.loads(merged_path.read_text(encoding="utf-8"))
    assert payload["artifacts"]["root"]["universe"] == "U73"
