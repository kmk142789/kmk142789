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
    assert pending_after_progress[0] == "forge_legacy_compass"
    assert evolver.state.network_cache["pending_steps"] == pending_after_progress
    after_log = evolver.state.event_log[-1]
    assert "persist_artifact=True" in after_log

    pending_without_artifact = evolver.pending_steps(persist_artifact=False)
    assert "write_artifact" not in pending_without_artifact
    assert evolver.state.network_cache["pending_steps"] == pending_without_artifact
    without_artifact_log = evolver.state.event_log[-1]
    assert "persist_artifact=False" in without_artifact_log


def test_sequence_plan_returns_structured_steps():
    evolver = EchoEvolver()

    plan = evolver.sequence_plan()
    assert plan[0]["step"] == "advance_cycle"
    assert plan[0]["status"] == "pending"
    assert plan[-1]["step"] == "write_artifact"
    assert evolver.state.network_cache["sequence_plan"] == plan

    plan[0]["status"] = "mutated"
    assert evolver.state.network_cache["sequence_plan"][0]["status"] == "pending"

    evolver.state.network_cache["completed_steps"].add("advance_cycle")
    updated_plan = evolver.sequence_plan()
    assert updated_plan[0]["status"] == "completed"

    plan_without_artifact = evolver.sequence_plan(persist_artifact=False)
    assert all(entry["step"] != "write_artifact" for entry in plan_without_artifact)

    summary = evolver.describe_sequence(persist_artifact=False)
    assert "EchoEvolver cycle sequence" in summary
    last_log = evolver.state.event_log[-1]
    assert f"({len(plan_without_artifact)} steps)" in last_log
