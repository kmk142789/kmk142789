from echo.echo_codox_kernel import PulseEvent
from echo.pulse_momentum import compute_pulse_momentum


def test_pulse_momentum_requires_history():
    now = 1_000.0
    events = [PulseEvent(timestamp=900.0, message="init")]

    forecast = compute_pulse_momentum(events, now=now)

    assert forecast.cadence_label == "insufficient"
    assert forecast.expected_next_timestamp is None
    assert forecast.time_since_last_seconds == 100.0
    assert forecast.drought_alert is False


def test_pulse_momentum_recognises_steady_cadence():
    events = [
        PulseEvent(timestamp=0.0, message="start"),
        PulseEvent(timestamp=3_600.0, message="tick"),
        PulseEvent(timestamp=7_200.0, message="tick"),
        PulseEvent(timestamp=10_800.0, message="tick"),
    ]

    forecast = compute_pulse_momentum(events, now=14_400.0, horizon_hours=24.0, lookback=10)

    assert forecast.sample_size == 3
    assert forecast.cadence_label in {"steady", "accelerating"}
    assert forecast.drought_alert is False
    assert forecast.expected_next_timestamp == 14_400.0
    assert forecast.horizon_coverage and forecast.horizon_coverage > 5
    assert forecast.confidence > 0.5


def test_pulse_momentum_flags_droughts_and_bursts():
    events = [
        PulseEvent(timestamp=0.0, message="seed"),
        PulseEvent(timestamp=600.0, message="burst-1"),
        PulseEvent(timestamp=1_200.0, message="burst-2"),
        PulseEvent(timestamp=7_200.0, message="long-gap"),
    ]

    forecast = compute_pulse_momentum(events, now=14_400.0, horizon_hours=12.0, lookback=4)

    assert forecast.cadence_label == "dormant"
    assert forecast.drought_alert is True
    assert forecast.burstiness > 0.3
    assert forecast.time_since_last_seconds == 7_200.0
    assert forecast.expected_next_timestamp == 7_800.0
