from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from echo_cli.pulse_analysis import (
    PulseEvent,
    build_pulse_timeline,
    categorize_message,
    load_pulse_history,
    summarize_pulse_activity,
)


def _event(hours: int, message: str, *, hash_prefix: str = "hash") -> PulseEvent:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return PulseEvent(timestamp=base + timedelta(hours=hours), message=message, hash=f"{hash_prefix}-{hours}")


def test_categorize_message_variants() -> None:
    assert categorize_message("🌀 evolve:manual:abc") == "manual"
    assert categorize_message("echo:pipeline") == "pipeline"
    assert categorize_message("  artifact  ") == "artifact"
    assert categorize_message("") == "unknown"


def test_summarize_pulse_activity_calculations() -> None:
    events = [
        _event(0, "pulse:manual:a"),
        _event(2, "pulse:github-action:b"),
        _event(26, "pulse:manual:c"),
    ]
    summary = summarize_pulse_activity(events)
    assert summary["total_events"] == 3
    assert summary["days_active"] == 2
    assert pytest.approx(summary["avg_interval_seconds"], rel=1e-3) == (26 * 3600) / 2
    assert summary["category_counts"]["manual"] == 2
    assert summary["category_counts"]["github-action"] == 1


def test_build_pulse_timeline_grouping() -> None:
    events = [
        _event(0, "pulse:manual:a"),
        _event(1, "pulse:manual:b"),
        _event(25, "pulse:auto:c"),
    ]
    day_rows = build_pulse_timeline(events, period="day")
    assert day_rows[0][1] == 1
    assert day_rows[1][1] == 2
    hour_rows = build_pulse_timeline(events, period="hour")
    assert any(row[0].endswith("00Z") for row in hour_rows)


def test_load_pulse_history_from_file(tmp_path: Path) -> None:
    payload = [
        {"timestamp": 1714828800.0, "message": "pulse:manual:alpha", "hash": "abc"},
        {"timestamp": 1714832400.0, "message": "pulse:deploy:beta", "hash": "def"},
    ]
    history_path = tmp_path / "pulse_history.json"
    history_path.write_text(json.dumps(payload), encoding="utf-8")
    events = load_pulse_history(history_path)
    assert len(events) == 2
    assert events[0].message.endswith("alpha")
    assert events[1].timestamp > events[0].timestamp
