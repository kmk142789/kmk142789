"""Unit tests for the pulse interactive session helpers."""

from __future__ import annotations

from tools.pulse_continuity_audit import PulseEvent
from tools.pulse_interactive import PulseSession, abbreviate_hash, format_event


def _event(timestamp: float, message: str, hash_value: str = "a" * 64) -> PulseEvent:
    return PulseEvent(timestamp=timestamp, message=message, hash=hash_value)


def test_latest_events_return_most_recent_first() -> None:
    session = PulseSession(
        [
            _event(100.0, "🌐 alpha:signal"),
            _event(200.0, "🌐 alpha:followup"),
            _event(150.0, "🛰️ beta:ping"),
        ]
    )
    recent = session.latest_events(limit=2)
    assert [event.timestamp for event in recent] == [200.0, 150.0]


def test_search_performs_case_insensitive_match() -> None:
    session = PulseSession(
        [
            _event(100.0, "🌀 evolve:manual:abc"),
            _event(110.0, "🌀 evolve:github-action:def"),
            _event(120.0, "🌈 bloom:manual"),
        ]
    )
    matches = session.search("GITHUB")
    assert [event.message for event in matches] == ["🌀 evolve:github-action:def"]


def test_prefix_counts_sort_by_frequency_then_name() -> None:
    session = PulseSession(
        [
            _event(100.0, "🌀 evolve:manual"),
            _event(101.0, "🌀 evolve:github"),
            _event(102.0, "🌈 bloom:manual"),
            _event(103.0, "🌈 bloom:extra"),
            _event(104.0, "🌌 cosmic:signal"),
        ]
    )
    counts = session.prefix_counts()
    assert counts == [("🌀 evolve", 2), ("🌈 bloom", 2), ("🌌 cosmic", 1)]


def test_format_event_displays_iso_timestamp_and_abbreviated_hash() -> None:
    event = _event(1.0, "🌀 evolve:test", hash_value="f" * 64)
    rendered = format_event(event)
    assert rendered.startswith("1970-01-01T00:00:01+00:00 | 🌀 evolve:test | ffff")
    assert "…" in rendered


def test_abbreviate_hash_preserves_short_values() -> None:
    assert abbreviate_hash("abcd", length=4) == "abcd"
