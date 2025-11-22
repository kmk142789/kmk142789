from echo_pulse_novum import PulseEvent
from echo_pulse_storyboard import (
    build_storyboard,
    segment_sessions,
    source_from_message,
    storyboard_as_dict,
)


def _event(timestamp: float, message: str) -> PulseEvent:
    return PulseEvent(timestamp=timestamp, message=message, hash=f"hash-{timestamp}")


def test_segment_sessions_breaks_on_gap():
    events = [
        _event(0, "🌀 evolve:manual:first"),
        _event(120, "🌀 evolve:manual:second"),
        _event(3000, "🌀 evolve:automation:third"),
    ]

    sessions = segment_sessions(events, max_gap_seconds=900)

    assert len(sessions) == 2
    assert len(sessions[0].events) == 2
    assert sessions[1].events[0].message == "🌀 evolve:automation:third"
    assert sessions[0].sources["manual"] == 2
    assert sessions[1].sources["automation"] == 1


def test_storyboard_builds_readable_summary():
    events = [
        _event(0, "🌀 evolve:manual:first"),
        _event(60, "🌀 evolve:automation:second"),
        _event(90, "🌀 evolve:experiment:third"),
    ]

    sessions = segment_sessions(events, max_gap_seconds=600)
    text = build_storyboard(sessions)

    assert "Sessions discovered : 1" in text
    assert "Sources     : manual×1, automation×1, experiment×1" in text
    assert "Cadence     :" in text

    data = storyboard_as_dict(sessions)
    assert data["sessions"][0]["sources"] == {
        "manual": 1,
        "automation": 1,
        "experiment": 1,
    }


def test_source_from_message_defaults_to_unknown():
    assert source_from_message("mystery event") == "unknown"
