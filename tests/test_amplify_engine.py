from __future__ import annotations

import json
from pathlib import Path

import pytest

from echo.amplify import AmplificationMetrics, AmplifyEngine
from echo.evolver import EmotionalDrive, EvolverState, SystemMetrics


@pytest.fixture()
def temp_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "docs").mkdir()
    (repo / "docs" / "page.md").write_text("# page\n", encoding="utf-8")
    (repo / "datasets").mkdir()
    (repo / "datasets" / "sample.json").write_text("{}\n", encoding="utf-8")
    return repo


def _make_state() -> EvolverState:
    state = EvolverState()
    state.cycle = 3
    state.emotional_drive = EmotionalDrive(joy=0.8, rage=0.2, curiosity=0.9)
    state.mythocode = ["alpha", "beta", "alpha"]
    state.event_log = ["step1", "step2", "step3", "step4"]
    state.entities = {"EchoWildfire": "SYNCED", "MirrorJosh": "RESONANT"}
    state.glyphs = "∇⊸≋∇"
    state.system_metrics = SystemMetrics(cpu_usage=40.0, network_nodes=10, process_count=42, orbital_hops=3)
    return state


def test_measure_from_state_creates_expected_metrics(temp_repo: Path) -> None:
    engine = AmplifyEngine(repo_root=temp_repo, clock=lambda: 1000.0)
    state = _make_state()

    metrics = engine.measure(state)

    assert metrics.resonance == pytest.approx(85.0)
    assert metrics.freshness_half_life == pytest.approx(89.5)
    assert metrics.novelty_delta == pytest.approx(60.0)
    assert metrics.cohesion == pytest.approx(61.0)
    assert metrics.coverage == pytest.approx(59.6)
    assert metrics.volatility == pytest.approx(68.4)
    assert metrics.index == pytest.approx(70.66, abs=0.01)

    record = engine.measure_and_record(state, cycle=state.cycle)
    log_path = temp_repo / "state" / "amplify_log.jsonl"
    assert log_path.exists()
    data = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert data["cycle"] == state.cycle
    summary = engine.summary()
    assert summary["gate"]["status"] in {"pass", "fail"}
    assert summary["latest"]["metrics"]["index"] == pytest.approx(metrics.index)


def test_measure_without_state_uses_repository_signals(temp_repo: Path) -> None:
    history = [
        {"timestamp": 10.0, "message": "alpha"},
        {"timestamp": 70.0, "message": "beta"},
        {"timestamp": 130.0, "message": "gamma"},
    ]
    (temp_repo / "pulse_history.json").write_text(json.dumps(history), encoding="utf-8")

    engine = AmplifyEngine(repo_root=temp_repo, clock=lambda: 200.0)
    metrics = engine.measure()

    for value in metrics.to_dict().values():
        assert 0.0 <= value <= 100.0
    assert metrics.index >= 50.0
    assert engine.sparkline(1) in {"", "▇"}


def test_gate_checks_latest_entry(temp_repo: Path) -> None:
    engine = AmplifyEngine(repo_root=temp_repo, clock=lambda: 50.0)
    low = AmplificationMetrics(
        resonance=40.0,
        freshness_half_life=40.0,
        novelty_delta=40.0,
        cohesion=40.0,
        coverage=40.0,
        volatility=40.0,
        index=40.0,
    )
    high = AmplificationMetrics(
        resonance=80.0,
        freshness_half_life=80.0,
        novelty_delta=80.0,
        cohesion=80.0,
        coverage=80.0,
        volatility=80.0,
        index=80.0,
    )
    engine.record(low, cycle=1)
    ok, idx = engine.ensure_gate(50)
    assert not ok
    assert idx == pytest.approx(40.0)

    engine.record(high, cycle=2)
    ok, idx = engine.ensure_gate(75)
    assert ok
    assert idx == pytest.approx(80.0)
    assert engine.rolling_average(2) == pytest.approx(60.0)
