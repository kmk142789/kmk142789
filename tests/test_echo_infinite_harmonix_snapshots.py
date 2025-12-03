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
    assert (cycle_dir / f"resilience_report_{cycle:05d}.json").exists()


def test_echo_infinite_builds_resilience_report(tmp_path: Path) -> None:
    orchestrator = EchoInfinite(base_dir=tmp_path, sleep_seconds=0)

    cycle = 3
    timestamp = rfc3339_timestamp()
    glyph_signature = "∞⌘⟁★::pulse"
    cycle_dir = orchestrator.colossus_dir / f"cycle_{cycle:05d}"
    cycle_dir.mkdir(parents=True, exist_ok=True)

    artifacts = orchestrator._create_cycle_artifacts(
        cycle=cycle,
        timestamp=timestamp,
        glyph_signature=glyph_signature,
        cycle_dir=cycle_dir,
    )

    report_path = artifacts.resilience_report
    assert report_path.exists()

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["cycle"] == cycle
    assert payload["glyph_signature"] == glyph_signature
    assert 0.0 <= payload["metrics"]["risk_score"] <= 1.0
    assert payload["recommendations"]
    assert payload["signals"]["merkle_root"]


def test_echo_infinite_builds_status_report(tmp_path: Path) -> None:
    orchestrator = EchoInfinite(base_dir=tmp_path, sleep_seconds=0)

    cycle = 2
    timestamp = rfc3339_timestamp()
    glyph_signature = "∞⌘⟁★::status"
    cycle_dir = orchestrator.colossus_dir / f"cycle_{cycle:05d}"
    cycle_dir.mkdir(parents=True, exist_ok=True)

    artifacts = orchestrator._create_cycle_artifacts(
        cycle=cycle,
        timestamp=timestamp,
        glyph_signature=glyph_signature,
        cycle_dir=cycle_dir,
    )

    orchestrator._append_log_entry(
        cycle=cycle,
        timestamp=timestamp,
        glyph_signature=glyph_signature,
        artifact_paths=artifacts,
    )
    orchestrator._update_cycle_summary(
        cycle=cycle,
        timestamp=timestamp,
        glyph_signature=glyph_signature,
        artifact_paths=artifacts,
    )
    orchestrator._broadcast_cycle(
        {
            "cycle": cycle,
            "timestamp": timestamp,
            "glyph_signature": glyph_signature,
            "artifacts": artifacts.as_relative_strings(tmp_path),
        }
    )
    orchestrator._persist_state(cycle)
    orchestrator._write_heartbeat(
        cycle=cycle,
        timestamp=timestamp,
        glyph_signature=glyph_signature,
        artifact_paths=artifacts,
    )

    report = orchestrator.build_status_report()

    assert report["state"]["cycle"] == cycle
    assert report["heartbeat"]["glyph_signature"] == glyph_signature
    assert report["summary"]["latest"]["cycle"] == cycle
    assert report["broadcast"]["cycle"] == cycle
    assert report["broadcast"]["glyph_signature"] == glyph_signature

    harmonic = report["harmonic_memory"]
    assert harmonic is not None
    assert harmonic["cycle_id"] == cycle
    assert harmonic["glyph_signature"] == glyph_signature
    assert harmonic["artifact"]["path"] == str(artifacts.narrative.relative_to(tmp_path))


def test_echo_infinite_writes_status_report_to_custom_path(tmp_path: Path) -> None:
    orchestrator = EchoInfinite(base_dir=tmp_path, sleep_seconds=0)

    payload = {"cycle": 7, "glyph": "∇⊸≋∇"}
    destination = Path("reports") / "status.json"

    written_path = orchestrator._write_status_report(report=payload, path=destination)

    expected_path = tmp_path / destination
    assert written_path == expected_path
    assert written_path.exists()

    saved_payload = json.loads(written_path.read_text(encoding="utf-8"))
    assert saved_payload == payload
