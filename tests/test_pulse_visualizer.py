from __future__ import annotations

from datetime import datetime, timedelta, timezone

from echo.pulse.visualizer import SignalPoint, build_signal_series


def test_build_signal_series_combines_sources() -> None:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    pulses = [
        {"timestamp": (base).isoformat()},
        {"timestamp": (base.replace(minute=30)).isoformat()},
        {"timestamp": (base.replace(hour=1)).isoformat()},
    ]
    repo_events = [base, base + timedelta(minutes=30)]
    thread_events = [base + timedelta(hours=1)]
    merge_events = [base + timedelta(hours=1, minutes=10)]
    series = build_signal_series(
        pulses=pulses,
        repo_events=repo_events,
        thread_events=thread_events,
        merge_events=merge_events,
        interval_minutes=60,
    )
    assert len(series) == 2
    first, second = series
    assert isinstance(first, SignalPoint)
    assert first.pulses == 2
    assert first.repo_activity == 2
    assert first.intensity == 2 + 2 + 0 + 0
    assert second.pulses == 1
    assert second.threads == 1
    assert second.merges == 1
    assert second.intensity == 1 + 0 + 1 + 2

