"""Tests for the EchoEvolver revolution status helper."""

from __future__ import annotations

import pytest

from echo.evolver import EchoEvolver


def _prime_evolver(minimal: bool = False) -> EchoEvolver:
    evolver = EchoEvolver()
    evolver.advance_cycle()
    evolver.mutate_code()
    evolver.emotional_modulation()
    evolver.generate_symbolic_language()
    evolver.invent_mythocode()
    if not minimal:
        evolver.system_monitor()
    return evolver


def test_revolution_status_includes_progress_and_history() -> None:
    evolver = _prime_evolver()

    status = evolver.revolution_status()
    log_without_marker = evolver.state.event_log[:-1]
    expected_history = list(log_without_marker[-len(status["history"]):])

    assert status["cycle"] == evolver.state.cycle
    assert status["progress"] > 0
    assert status["history"] == expected_history
    assert status["quantum_key_ready"] is False
    assert status["next_step"].startswith("Next step:")
    assert status["summary"].startswith(f"Cycle {evolver.state.cycle}")
    assert evolver.state.event_log[-1].startswith("Revolution status charted")


def test_revolution_status_history_limit_and_validation() -> None:
    evolver = _prime_evolver(minimal=True)

    status = evolver.revolution_status(history_limit=2)
    log_without_marker = evolver.state.event_log[:-1]
    expected_tail = list(log_without_marker[-len(status["history"]):])

    assert status["history"] == expected_tail
    assert len(status["history"]) == len(expected_tail)

    with pytest.raises(ValueError):
        evolver.revolution_status(history_limit=-1)

    empty = evolver.revolution_status(history_limit=0)
    assert empty["history"] == []
