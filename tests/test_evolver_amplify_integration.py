import random
from pathlib import Path

import pytest

from echo import JsonMemoryStore
from echo.amplify import AmplifyEngine
from echo.evolver import EchoEvolver


def _time_sequence(values):
    iterator = iter(values)

    def _next() -> float:
        return next(iterator)

    return _next


def _memory_store(tmp_path: Path) -> JsonMemoryStore:
    return JsonMemoryStore(
        storage_path=tmp_path / "memory.json",
        log_path=tmp_path / "log.md",
        core_datasets={},
    )


def test_cycle_run_records_snapshot(tmp_path: Path):
    engine = AmplifyEngine(
        log_path=tmp_path / "amplify.jsonl",
        manifest_path=tmp_path / "manifest.json",
        time_source=_time_sequence([1_000.0]),
        commit_resolver=lambda: "integrate",
    )
    evolver = EchoEvolver(
        rng=random.Random(0),
        time_source=lambda: 42,
        amplify_engine=engine,
        memory_store=_memory_store(tmp_path),
    )

    evolver.run(persist_artifact=False)

    snapshot = engine.latest_snapshot()
    assert snapshot is not None
    assert snapshot.cycle == evolver.state.cycle
    assert "amplify_snapshot" in evolver.state.network_cache
    assert (tmp_path / "amplify.jsonl").exists()
    manifest = (tmp_path / "manifest.json").read_text(encoding="utf-8")
    assert "amplification" in manifest


def test_amplify_gate_enforced(tmp_path: Path):
    zero_weights = {
        "resonance": 0.0,
        "freshness_half_life": 0.0,
        "novelty_delta": 0.0,
        "cohesion": 0.0,
        "coverage": 0.0,
        "stability": 0.0,
    }
    engine = AmplifyEngine(
        log_path=tmp_path / "gate.jsonl",
        manifest_path=tmp_path / "gate_manifest.json",
        weights=zero_weights,
        time_source=_time_sequence([1_000.0, 1_200.0, 1_400.0]),
        commit_resolver=lambda: "gate",
    )
    evolver = EchoEvolver(
        rng=random.Random(1),
        time_source=lambda: 99,
        amplify_engine=engine,
        memory_store=_memory_store(tmp_path),
    )

    with pytest.raises(RuntimeError, match="Amplify gate"):
        evolver.run_cycles(3, persist_artifacts=False, amplify_gate=10.0)

    assert len(engine.snapshots) == 3
