from datetime import datetime, timezone

import pytest

from tools.pulse_history_summary import (
    _format_prefix_table,
    summarize_pulse_history,
)


def test_summarize_pulse_history_basic():
    entries = [
        {"timestamp": 1, "message": "🌟 start:alpha"},
        {"timestamp": 4, "message": "🌟 start:beta"},
        {"timestamp": 10, "message": "🔥 change:gamma"},
    ]

    summary = summarize_pulse_history(entries)

    assert summary.count == 3
    assert summary.first_message == "🌟 start:alpha"
    assert summary.last_message == "🔥 change:gamma"

    expected_first = datetime.fromtimestamp(1, tz=timezone.utc).isoformat()
    expected_last = datetime.fromtimestamp(10, tz=timezone.utc).isoformat()
    assert summary.first_timestamp == expected_first
    assert summary.last_timestamp == expected_last
    assert summary.average_interval_seconds == pytest.approx(4.5)
    assert summary.prefix_counts == {"🌟 start": 2, "🔥 change": 1}


def test_summarize_pulse_history_empty():
    with pytest.raises(ValueError):
        summarize_pulse_history([])


def test_format_prefix_table_limit():
    table = _format_prefix_table({"b": 2, "a": 1, "": 3}, limit=2)
    lines = table.splitlines()
    assert lines == ["- b :: 2", "- a :: 1"]
