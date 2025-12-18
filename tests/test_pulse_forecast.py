from datetime import datetime, timezone

from echo.echo_codox_kernel import PulseEvent
from echo.pulse.forecast import forecast_pulse_activity


def _ts(seconds: int) -> float:
    return float(seconds)


def test_forecast_empty_history_flags_empty():
    forecast = forecast_pulse_activity([], now=_ts(0))

    assert forecast.risk_level == "empty"
    assert forecast.projected_events == 0
    assert "Seed the first pulse" in (forecast.recommendations[0] if forecast.recommendations else "")


def test_forecast_projects_events_and_risk():
    events = [
        PulseEvent(timestamp=_ts(0), message="start"),
        PulseEvent(timestamp=_ts(100), message="checkpoint"),
        PulseEvent(timestamp=_ts(200), message="complete"),
    ]

    forecast = forecast_pulse_activity(
        events,
        now=_ts(280),
        warning_hours=0.02,  # ~72 seconds
        critical_hours=0.06,  # ~216 seconds
        horizon_hours=0.1,  # 6 minutes
    )

    assert forecast.metrics.cadence_rating == "steady"
    assert forecast.risk_level == "warning"
    assert forecast.projected_events >= 2

    expected_iso = datetime.fromtimestamp(300, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    assert forecast.expected_next_iso == expected_iso

    assert any("pulses" in rec for rec in forecast.recommendations)
