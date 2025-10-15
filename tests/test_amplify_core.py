import json
from pathlib import Path

import pytest

from echo.amplify import AmplifyEngine
from echo.evolver import EmotionalDrive, EvolverState, SystemMetrics


def _time_source(values):
    iterator = iter(values)

    def _next() -> float:
        return next(iterator)

    return _next


def _state_template() -> EvolverState:
    state = EvolverState()
    state.cycle = 1
    state.emotional_drive = EmotionalDrive(joy=0.8, rage=0.1, curiosity=0.9)
    state.system_metrics = SystemMetrics(cpu_usage=20.0, network_nodes=10, process_count=33, orbital_hops=3)
    state.mythocode = ["alpha", "beta"]
    return state


def test_snapshot_metrics_and_manifest(tmp_path: Path):
    log_path = tmp_path / "amplify.jsonl"
    manifest_path = tmp_path / "manifest.json"
    engine = AmplifyEngine(
        log_path=log_path,
        manifest_path=manifest_path,
        time_source=_time_source([1_000.0, 1_900.0]),
        commit_resolver=lambda: "commit-hash",
    )

    state = _state_template()
    engine.before_cycle(cycle=1)
    snapshot1, nudges1 = engine.after_cycle(
        cycle=1,
        state=state,
        digest={"progress": 1.0},
    )

    assert nudges1 == []
    assert snapshot1.metrics["resonance"] == 85.0
    assert snapshot1.metrics["freshness_half_life"] == 100.0
    assert snapshot1.metrics["coverage"] == 100.0
    expected_index = sum(
        snapshot1.metrics[key] * engine.weights.get(key, 0.0)
        for key in snapshot1.metrics
        if key != "stability"
    )
    volatility = 100.0 - snapshot1.metrics["stability"]
    expected_index -= engine.weights.get("stability", 0.0) * volatility
    assert snapshot1.index == pytest.approx(expected_index, abs=0.01)

    state.cycle = 2
    state.emotional_drive = EmotionalDrive(joy=0.7, rage=0.2, curiosity=0.88)
    state.mythocode = ["alpha", "gamma"]
    state.system_metrics = SystemMetrics(cpu_usage=24.0, network_nodes=12, process_count=40, orbital_hops=5)

    engine.before_cycle(cycle=2)
    snapshot2, nudges2 = engine.after_cycle(
        cycle=2,
        state=state,
        digest={"progress": 0.6},
    )

    assert snapshot2.metrics["freshness_half_life"] < 100.0
    assert snapshot2.metrics["novelty_delta"] == pytest.approx(50.0, abs=0.01)
    assert "Coverage slump" in nudges2[0]

    history = engine.snapshots
    assert len(history) == 2
    assert engine.rolling_average(window=2) == pytest.approx(
        (snapshot1.index + snapshot2.index) / 2, abs=0.001
    )

    log_lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(log_lines) == 2

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["amplification"]["latest"] == snapshot2.index
    assert manifest["amplification"]["rolling_avg"] == pytest.approx(
        round(engine.rolling_average(window=3), 2),
        abs=0.001,
    )
