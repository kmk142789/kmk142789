from __future__ import annotations

import random

import pytest

from echo.evolver import EchoEvolver


def test_evolution_status_initial_snapshot():
    evolver = EchoEvolver(rng=random.Random(0))

    status = evolver.evolution_status()

    assert status["cycle"] == 0
    assert status["progress"] == 0.0
    assert status["pending_steps"][0] == "advance_cycle"
    assert status["narrative_excerpt"] == ""
    assert status["system_metrics"] == {
        "cpu_usage": 0.0,
        "network_nodes": 0,
        "process_count": 0,
        "orbital_hops": 0,
    }
    assert status["recent_events"], "Expected digest event to be captured"
    assert "Cycle digest computed" in status["recent_events"][-1]

    assert evolver.state.network_cache["evolution_status"] == status
    assert evolver.state.event_log[-1] == "Evolution status summarized (cycle=0)"


def test_evolution_status_tracks_progress_and_event_window():
    evolver = EchoEvolver(rng=random.Random(0))
    evolver.advance_cycle()
    evolver.mutate_code()
    evolver.state.event_log.extend(["custom-1", "custom-2", "custom-3"])
    evolver.state.narrative = "🔥 Cycle 1: forged\nMore lines below"

    status = evolver.evolution_status(last_events=2)

    assert status["cycle"] == 1
    assert "advance_cycle" in status["completed_steps"]
    assert status["pending_steps"][0] == "emotional_modulation"
    assert status["narrative_excerpt"] == "🔥 Cycle 1: forged"
    assert len(status["recent_events"]) == 2
    assert status["recent_events"][0] == "custom-3"
    assert "Cycle digest computed" in status["recent_events"][1]

    with pytest.raises(ValueError):
        evolver.evolution_status(last_events=-1)
