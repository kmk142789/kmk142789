import json
from pathlib import Path

from echo_infinite import EchoInfinite, rfc3339_timestamp


def test_echo_infinite_persists_harmonix_snapshot(tmp_path: Path) -> None:
    orchestrator = EchoInfinite(base_dir=tmp_path, sleep_seconds=0)

    cycle = 1
    timestamp = rfc3339_timestamp()
    glyph_signature = "∇⊸≋∇::test"
    cycle_dir = orchestrator.colossus_dir / f"cycle_{cycle:05d}"
    cycle_dir.mkdir(parents=True, exist_ok=True)

    artifacts = orchestrator._create_cycle_artifacts(
        cycle=cycle,
        timestamp=timestamp,
        glyph_signature=glyph_signature,
        cycle_dir=cycle_dir,
    )

    snapshot_path = orchestrator.last_snapshot_path
    assert snapshot_path is not None
    assert snapshot_path.exists()

    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))

    cycle_snapshot = payload["cycle_snapshot"]
    assert cycle_snapshot["cycle_id"] == cycle

    state_block = cycle_snapshot["state"]
    assert state_block["glyph_signature"] == glyph_signature
    assert state_block["cycle"] == cycle

    emotions = state_block["emotional_vectors"]
    assert set(emotions.keys()) == {"joy", "curiosity", "rage"}
    assert all(0.0 <= value <= 1.0 for value in emotions.values())

    payload_block = cycle_snapshot["payload"]
    assert payload_block["glyph_signature"] == glyph_signature
    assert payload_block["emotional_vectors"] == emotions
    assert payload_block["dataset"]["cycle"] == cycle

    narrative_rel_path = artifacts.narrative.relative_to(tmp_path)
    assert cycle_snapshot["artifact"]["path"] == str(narrative_rel_path)

    expected_snapshot_path = tmp_path / "harmonic_memory" / "cycles" / "cycle_00001.json"
    assert snapshot_path == expected_snapshot_path


def test_echo_infinite_skips_fractal_nodes_when_disabled(tmp_path: Path) -> None:
    orchestrator = EchoInfinite(
        base_dir=tmp_path, sleep_seconds=0, write_fractal_nodes=False
    )

    cycle = 1
    timestamp = rfc3339_timestamp()
    glyph_signature = "∇⊸≋∇::test"
    cycle_dir = orchestrator.colossus_dir / f"cycle_{cycle:05d}"
    cycle_dir.mkdir(parents=True, exist_ok=True)

    orchestrator._create_cycle_artifacts(
        cycle=cycle,
        timestamp=timestamp,
        glyph_signature=glyph_signature,
        cycle_dir=cycle_dir,
    )

    assert not (cycle_dir / "puzzle_fractal").exists()
    assert not (cycle_dir / "dataset_fractal").exists()
    assert not (cycle_dir / "narrative_fractal").exists()
    assert not (cycle_dir / "lineage_fractal").exists()

    assert (cycle_dir / f"puzzle_cycle_{cycle:05d}.md").exists()
    assert (cycle_dir / f"dataset_cycle_{cycle:05d}.json").exists()
    assert (cycle_dir / f"glyph_narrative_{cycle:05d}.md").exists()
    assert (cycle_dir / f"lineage_map_{cycle:05d}.json").exists()
    assert (cycle_dir / f"verify_cycle_{cycle:05d}.py").exists()
    assert (cycle_dir / f"extraordinary_manifest_{cycle:05d}.json").exists()
