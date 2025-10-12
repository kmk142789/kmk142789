from datetime import datetime, timezone

import pytest

from echo_pulse_novum import (
    PulseEvent,
    build_report,
    novelty_highlight,
    pulse_intervals,
    sparkline,
)


def make_event(offset: int, message: str) -> PulseEvent:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()
    return PulseEvent(timestamp=base + offset, message=message, hash=f"hash{offset}")


def test_pulse_intervals_and_sparkline_basic():
    events = [make_event(0, "start"), make_event(10, "mid"), make_event(25, "end")]
    intervals = pulse_intervals(events)
    assert intervals == [10, 15]
    # Sparkline should contain exactly one of the predefined bar characters.
    assert sparkline(intervals) in {"▆█", "▇█", "▅█", "▄█", "▂█", "▃█"}


def test_sparkline_handles_zero_and_empty():
    assert sparkline([]) == "·"
    assert sparkline([0, 0]) == "··"


def test_novelty_highlight_variants():
    empty = novelty_highlight([])
    assert "No pulse events" in empty

    single = novelty_highlight([make_event(0, "solo")])
    assert "Only a single pulse" in single

    multi = novelty_highlight([make_event(0, "first"), make_event(30, "second")])
    assert "30s pause" in multi


def test_build_report_summary():
    events = [make_event(0, "first"), make_event(60, "second"), make_event(120, "third")]
    report = build_report(events)
    assert "Echo Pulse Novum" in report
    assert "Events logged : 3" in report
    assert "Mean gap (s)   : 60.00" in report
    assert "Tempo sparkline" in report
