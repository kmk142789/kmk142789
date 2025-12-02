from datetime import datetime, timezone

from echo.pulse_health import compute_pulse_metrics
from echo.echo_codox_kernel import PulseEvent


def _ts(seconds: int) -> float:
    return float(seconds)


def test_pulse_metrics_empty_history():
    metrics = compute_pulse_metrics([])

    assert metrics.total_events == 0
    assert metrics.cadence_score is None
    assert metrics.cadence_rating == "unknown"
    assert metrics.expected_next_timestamp is None
    assert metrics.overdue_seconds is None


def test_pulse_metrics_expected_projection_and_overdue():
    events = [
        PulseEvent(timestamp=_ts(0), message="start"),
        PulseEvent(timestamp=_ts(100), message="checkpoint"),
        PulseEvent(timestamp=_ts(200), message="complete"),
    ]

    metrics = compute_pulse_metrics(events, now=_ts(400))

    assert metrics.cadence_score == 100.0
    assert metrics.cadence_rating == "steady"
    assert metrics.expected_next_timestamp == 300
    assert metrics.overdue_seconds == 100
    assert metrics.expected_next_timestamp_iso == datetime.fromtimestamp(
        300, tz=timezone.utc
    ).isoformat().replace("+00:00", "Z")


def test_pulse_metrics_variability_score():
    events = [
        PulseEvent(timestamp=_ts(0), message="start"),
        PulseEvent(timestamp=_ts(10), message="spike"),
        PulseEvent(timestamp=_ts(210), message="drift"),
        PulseEvent(timestamp=_ts(610), message="recovery"),
    ]

    metrics = compute_pulse_metrics(events, now=_ts(610))

    assert metrics.cadence_rating == "variable"
    assert 50 <= (metrics.cadence_score or 0) <= 70
    assert metrics.overdue_seconds == 0
