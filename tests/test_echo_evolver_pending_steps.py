"""Tests for :meth:`echo.evolver.EchoEvolver.pending_steps`."""

from __future__ import annotations

from echo.evolver import EchoEvolver


def test_pending_steps_tracks_progress_and_event_log():
    evolver = EchoEvolver()

    pending_initial = evolver.pending_steps()
    assert pending_initial[0] == "advance_cycle"
    initial_log = evolver.state.event_log[-1]
    assert "Pending steps evaluated" in initial_log
    assert str(len(pending_initial)) in initial_log

    evolver.advance_cycle()
    evolver.mutate_code()
    evolver.emotional_modulation()

    pending_after_progress = evolver.pending_steps()
    assert "advance_cycle" not in pending_after_progress
    assert pending_after_progress[0] == "generate_symbolic_language"
    assert evolver.state.network_cache["pending_steps"] == pending_after_progress
    after_log = evolver.state.event_log[-1]
    assert "persist_artifact=True" in after_log

    pending_without_artifact = evolver.pending_steps(persist_artifact=False)
    assert "write_artifact" not in pending_without_artifact
    assert evolver.state.network_cache["pending_steps"] == pending_without_artifact
    without_artifact_log = evolver.state.event_log[-1]
    assert "persist_artifact=False" in without_artifact_log
