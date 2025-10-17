from __future__ import annotations

import random
from datetime import datetime, timezone

import pytest

from echo.amplify import AmplificationEngine
from echo.evolver import EchoEvolver


def _build_evolver(**kwargs) -> EchoEvolver:
    rng = random.Random(42)
    evolver = EchoEvolver(rng=rng, time_source=lambda: 123456789, **kwargs)
    evolver.advance_cycle()
    evolver.mutate_code()
    evolver.emotional_modulation()
    evolver.generate_symbolic_language()
    evolver.invent_mythocode()
    evolver.system_monitor()
    return evolver


def test_amplify_evolution_projects_state() -> None:
    evolver = _build_evolver()
    report = evolver.amplify_evolution(resonance_factor=1.5, preview_events=2)

    assert report["cycle"] == evolver.state.cycle
    assert report["next_step"].startswith("Next step:")
    assert report["remaining_steps"]
    assert len(report["propagation_preview"]) <= 2

    amplified = report["amplified_emotions"]
    assert amplified["joy"] >= evolver.state.emotional_drive.joy
    assert amplified["curiosity"] >= evolver.state.emotional_drive.curiosity

    cached = evolver.state.network_cache["amplified_evolution"]
    assert cached is report


def test_amplify_evolution_validates_inputs() -> None:
    evolver = _build_evolver()

    with pytest.raises(ValueError):
        evolver.amplify_evolution(resonance_factor=0)

    with pytest.raises(ValueError):
        evolver.amplify_evolution(preview_events=-1)


def test_amplify_evolution_projects_amplification_metrics(tmp_path) -> None:
    log_path = tmp_path / "amp" / "log.jsonl"
    engine = AmplificationEngine(
        log_path=log_path,
        manifest_path=tmp_path / "manifest.json",
        commit_source=lambda: "test-sha",
        time_source=lambda: datetime(2025, 5, 11, tzinfo=timezone.utc),
    )
    evolver = _build_evolver(amplifier=engine)

    report = evolver.amplify_evolution(resonance_factor=1.2)

    amplification = report.get("amplification")
    assert amplification is not None
    assert isinstance(amplification["index"], float)
    assert set(amplification["metrics"]) >= {
        "resonance",
        "freshness_half_life",
        "novelty_delta",
        "cohesion",
        "coverage",
        "stability",
    }
    assert amplification["commit_sha"] == "test-sha"
    assert isinstance(amplification["nudges"], list)
