from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from tools.pulse_continuity_audit import PulseEvent
from tools.pulse_resonance_forecast import generate_forecast


def _event(timestamp: float) -> PulseEvent:
    return PulseEvent(timestamp=timestamp, message="pulse", hash="hash")


def test_generate_forecast_produces_expected_schedule():
    base = 1_700_000_000
    events = [_event(base + 3600 * index) for index in range(4)]

    forecast = generate_forecast(events, future_count=2)

    assert forecast.history_count == 4
    assert forecast.interval_count == 3
    assert pytest.approx(forecast.average_interval, rel=1e-9) == 3600.0
    assert forecast.stddev_interval == pytest.approx(0.0, abs=1e-9)
    assert len(forecast.forecast) == 2

    first = forecast.forecast[0]
    expected_first_time = events[-1].moment + timedelta(seconds=3600)
    assert first.index == 1
    assert first.expected_time == expected_first_time
    assert first.confidence == 1.0

    second = forecast.forecast[1]
    expected_second_time = expected_first_time + timedelta(seconds=3600)
    assert second.expected_time == expected_second_time
    assert second.confidence == 1.0


def test_forecast_respects_custom_now_origin():
    base = 1_700_100_000
    events = [_event(base + 5400 * index) for index in range(3)]

    now = datetime.fromtimestamp(base + 5400 * 2, tz=timezone.utc) + timedelta(hours=2)
    forecast = generate_forecast(events, future_count=1, now=now)

    assert forecast.forecast
    first = forecast.forecast[0]
    assert first.expected_time == now + timedelta(seconds=5400)


def test_forecast_handles_empty_history():
    forecast = generate_forecast([], future_count=2)

    assert forecast.forecast == []
    assert "pulse history is empty" in forecast.warnings
