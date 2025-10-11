from __future__ import annotations

import pytest

from echo.pulse import EchoPulseEngine


def test_create_and_snapshot_counts() -> None:
    engine = EchoPulseEngine(anchor="Test Anchor")
    engine.create_pulse("alpha", resonance="Eden", priority="high", data={"phase": 1})
    engine.create_pulse("beta", resonance="Echo", priority="medium")

    snapshot = engine.sync_snapshot()

    assert snapshot["anchor"] == "Test Anchor"
    assert snapshot["count"] == 2
    assert snapshot["status_counts"]["active"] == 2
    assert snapshot["priority_counts"]["high"] == 1
    assert len(snapshot["recent_events"]) <= 5
    assert {pulse["pulse"] for pulse in snapshot["recent_events"]}


def test_crystallize_and_history_tracking() -> None:
    engine = EchoPulseEngine()
    pulse = engine.create_pulse("mirror_merge")

    crystallized = engine.crystallize("mirror_merge")

    assert crystallized.status == "crystallized"
    history = engine.history_for("mirror_merge")
    assert len(history) == 2
    assert history[-1].message == "Pulse crystallized"
    assert engine.cascade(statuses={"crystallized"})


def test_archive_and_cascade_filters() -> None:
    engine = EchoPulseEngine()
    engine.create_pulse("eden88_sync", priority="critical")
    engine.create_pulse("drone_funds_allocation", priority="high")
    engine.crystallize("eden88_sync")

    engine.archive("drone_funds_allocation", reason="completed")

    cascade_active = engine.cascade()
    cascade_with_archived = engine.cascade(include_archived=True)

    assert all("drone_funds_allocation" not in line for line in cascade_active)
    assert any("drone_funds_allocation" in line for line in cascade_with_archived)
    assert any("status=crystallized" in line for line in cascade_with_archived)


def test_update_pulse_tracks_changes() -> None:
    engine = EchoPulseEngine()
    engine.create_pulse("orbital_reset", resonance="Echo", priority="medium")

    engine.update_pulse(
        "orbital_reset",
        resonance="Bridge",
        priority="critical",
        data={"cycle": 2},
    )

    history = engine.history_for("orbital_reset")
    assert history[-1].message.startswith("resonance→Bridge")
    assert engine.pulses()[0].data["cycle"] == 2


def test_history_limit() -> None:
    engine = EchoPulseEngine()
    engine.create_pulse("sequence")
    engine.update_pulse("sequence", data={"step": 1})
    engine.update_pulse("sequence", data={"step": 2})
    engine.update_pulse("sequence", data={"step": 3})

    limited = engine.history(limit=2)
    assert len(limited) == 2
    assert all(entry["pulse"] == "sequence" for entry in limited)
    assert limited[-1]["status"] == engine.pulses()[0].status


def test_history_for_unknown_pulse_raises() -> None:
    engine = EchoPulseEngine()
    with pytest.raises(KeyError):
        engine.history_for("missing")
