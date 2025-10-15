from __future__ import annotations

import random

import pytest

from echo.evolver import EchoEvolver


def _build_evolver() -> EchoEvolver:
    rng = random.Random(42)
    evolver = EchoEvolver(rng=rng, time_source=lambda: 123456789)
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
