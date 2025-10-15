import json
import random
from datetime import datetime, timezone
from pathlib import Path

import pytest

from echo.amplify import AmplificationEngine
from echo.evolver import EchoEvolver


def _build_engine(tmp_path: Path) -> AmplificationEngine:
    log_path = tmp_path / "amplify.jsonl"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"format": "test"}), encoding="utf-8")
    commit_sha = "feedcafe" * 5
    return AmplificationEngine(
        log_path=log_path,
        manifest_path=manifest_path,
        timestamp_source=lambda: datetime(2024, 3, 1, tzinfo=timezone.utc),
        commit_resolver=lambda: (commit_sha, "2024-03-01T00:00:00Z"),
    )


def test_evolver_records_amplification_snapshot(tmp_path: Path) -> None:
    engine = _build_engine(tmp_path)
    evolver = EchoEvolver(
        artifact_path=tmp_path / "artifact.json",
        rng=random.Random(2),
        time_source=lambda: 123456789,
        amplify_engine=engine,
    )

    state = evolver.run(enable_network=False, persist_artifact=False)
    snapshot = state.network_cache.get("amplify_snapshot")
    nudges = state.network_cache.get("amplify_nudges")

    assert snapshot is not None
    assert isinstance(snapshot, dict)
    assert snapshot["cycle"] == state.cycle
    assert "index" in snapshot
    assert isinstance(nudges, list)

    log_lines = engine.log_path.read_text(encoding="utf-8").strip().splitlines()
    assert log_lines

    manifest = json.loads(engine.manifest_path.read_text(encoding="utf-8"))
    assert manifest["amplification"]["latest"]["cycle"] == state.cycle


def test_run_cycles_enforces_gate(tmp_path: Path) -> None:
    engine = _build_engine(tmp_path)
    evolver = EchoEvolver(
        artifact_path=tmp_path / "artifact.json",
        rng=random.Random(3),
        time_source=lambda: 123456789,
        amplify_engine=engine,
    )

    evolver.run(enable_network=False, persist_artifact=False)

    snapshots = evolver.run_cycles(1, persist_artifacts=False, amplify_gate=5.0)
    assert len(snapshots) == 1

    manifest = json.loads(engine.manifest_path.read_text(encoding="utf-8"))
    assert manifest["amplification"]["gate"] == 5.0

    with pytest.raises(RuntimeError):
        evolver.run_cycles(1, persist_artifacts=False, amplify_gate=95.0)
