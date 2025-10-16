from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from echo.amplify import AmplificationEngine, AmplifyGateError
from echo.evolver import EchoEvolver


def incremental_time():
    base = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
    counter = {"value": -1}

    def _next() -> datetime:
        counter["value"] += 1
        return base + timedelta(minutes=counter["value"])

    return _next


@pytest.fixture()
def engine(tmp_path: Path) -> AmplificationEngine:
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    return AmplificationEngine(
        log_path=tmp_path / "log.jsonl",
        manifest_path=manifest,
        time_source=incremental_time(),
        commit_source=lambda: "deadbeef",
    )


def test_run_cycles_produces_snapshots(engine: AmplificationEngine, tmp_path: Path) -> None:
    evolver = EchoEvolver(rng=None, amplifier=engine)
    results = evolver.run_cycles(3, persist_artifact=False)
    assert len(results) == 3
    history = engine.load_history()
    assert len(history) == 3
    assert engine.manifest_path.exists()
    data = engine.manifest_path.read_text(encoding="utf-8")
    assert "amplification" in data

    with pytest.raises(AmplifyGateError):
        evolver.run_cycles(1, persist_artifact=False, amplify_gate=200.0)

    evolver.run_cycles(1, persist_artifact=False, amplify_gate=5.0)
