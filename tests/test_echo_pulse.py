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


def test_universal_advancement_report() -> None:
    engine = EchoPulseEngine(anchor="Advancement Anchor")
    engine.create_pulse("alpha", priority="critical", data={"cycle": 1})
    engine.update_pulse("alpha", data={"cycle": 2})

    engine.create_pulse("beta", priority="low")
    engine.crystallize("beta")

    engine.create_pulse("gamma", priority="medium")
    engine.archive("gamma", reason="retired")

    report_active = engine.universal_advancement()
    report_all = engine.universal_advancement(include_archived=True)

    assert report_active["anchor"] == "Advancement Anchor"
    assert report_active["total_pulses"] == 2
    assert report_active["advancement_score"] > 0
    assert report_active["status_breakdown"]["active"] == 1
    assert any(focus["pulse"] == "alpha" for focus in report_active["enhancement_focus"])

    assert report_all["total_pulses"] == 3
    assert report_all["status_breakdown"]["active"] == 1
    assert report_all["status_breakdown"]["crystallized"] == 1
    assert report_all["status_breakdown"]["archived"] == 1


def test_universal_advancement_on_empty_engine() -> None:
    engine = EchoPulseEngine()
    report = engine.universal_advancement()

    assert report["total_pulses"] == 0
    assert report["advancement_score"] == 0.0
    assert report["enhancement_focus"] == []

def test_create_enhance_and_advance_summary_tracks_creation_and_advancement() -> None:
    engine = EchoPulseEngine(anchor="Portal Anchor")
    engine.create_pulse("alpha", priority="critical")
    engine.create_pulse("beta", priority="low")
    engine.crystallize("beta")
    engine.archive("beta", reason="complete")

    summary = engine.create_enhance_and_advance(
        include_archived=True, creation_limit=2, focus_limit=1
    )

    assert summary["anchor"] == "Portal Anchor"

    created = summary["created"]
    assert created["total_active"] == 1
    assert created["total_archived"] == 1
    assert len(created["recent_highlights"]) == 2
    assert created["recent_highlights"][0]["status"] == "archived"
    assert created["recent_highlights"][0]["hash"].isalnum()

    enhancement = summary["enhancement"]
    assert enhancement["focus_limit"] == 1
    assert 0.0 <= enhancement["recommendation_coverage"] <= 1.0

    advancement = summary["advancement"]
    assert advancement["include_archived"] is True
    assert advancement["total_pulses"] == 2
    assert advancement["status_breakdown"]["archived"] == 1


def test_create_enhance_and_advance_limits_and_validation() -> None:
    engine = EchoPulseEngine()
    engine.create_pulse("alpha")

    summary = engine.create_enhance_and_advance(creation_limit=0, focus_limit=0)
    assert summary["created"]["recent_highlights"] == []
    assert summary["enhancement"]["focus"] == []
    assert summary["enhancement"]["recommendation_coverage"] == 0.0

    with pytest.raises(ValueError):
        engine.create_enhance_and_advance(creation_limit=-1)

    with pytest.raises(ValueError):
        engine.create_enhance_and_advance(focus_limit=-1)
