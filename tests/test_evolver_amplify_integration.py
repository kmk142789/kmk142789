from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from echo.evolver import EchoEvolver


def _ns_clock(start: int = 1_700_000_000_000_000_000, step: int = 500_000_000) -> callable:
    value = start

    def _tick() -> int:
        nonlocal value
        current = value
        value += step
        return current

    return _tick


def test_after_cycle_records_snapshot(tmp_path: Path) -> None:
    evolver = EchoEvolver(
        artifact_path=tmp_path / "artifact.echo.json",
        repo_root=tmp_path,
        rng=random.Random(3),
        time_source=_ns_clock(),
    )
    evolver.amplification_engine.thresholds = {key: 0.95 for key in evolver.amplification_engine.thresholds}

    evolver.run(enable_network=False, persist_artifact=False)

    latest = evolver.state.network_cache.get("amplify_latest_snapshot")
    assert latest
    assert latest["cycle"] == evolver.state.cycle

    nudges = evolver.state.network_cache.get("amplify_nudges")
    assert isinstance(nudges, list)
    assert any("Amplify nudge" in message for message in evolver.state.event_log)

    log_path = tmp_path / "state" / "amplify_log.jsonl"
    assert log_path.exists()
    entries = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line]
    assert entries and entries[0]["cycle"] == evolver.state.cycle


def test_run_cycles_enforces_gate(tmp_path: Path) -> None:
    evolver = EchoEvolver(
        artifact_path=tmp_path / "artifact.echo.json",
        repo_root=tmp_path,
        rng=random.Random(4),
        time_source=_ns_clock(),
    )

    with pytest.raises(RuntimeError) as excinfo:
        evolver.run_cycles(
            3,
            enable_network=False,
            persist_artifacts=False,
            amplify_gate=95.0,
        )
    assert "Amplify gate" in str(excinfo.value)

    history = list(evolver.amplification_engine.history)
    assert len(history) >= 1

    evolver.run_cycles(
        2,
        enable_network=False,
        persist_artifacts=False,
        amplify_gate=20.0,
    )
    history_after = list(evolver.amplification_engine.history)
    assert len(history_after) >= len(history) + 2

    assert "amplify_gate_target" not in evolver.state.network_cache
