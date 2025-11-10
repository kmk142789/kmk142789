from __future__ import annotations

from echo.luminal_horizon import (
    HorizonForecast,
    HorizonSignal,
    LuminalHorizon,
    render_horizon_map,
)


def test_project_generates_forecast() -> None:
    horizon = LuminalHorizon(baseline_pulse=0.35, coherence_bias=0.7)
    signals = [
        HorizonSignal("Aurora Thread", luminosity=0.8, confidence=0.65, motifs=("aurora", "north")),
        HorizonSignal("Tidal Whisper", luminosity=0.55, confidence=0.9, motifs=("tidal",)),
    ]

    forecast = horizon.project(signals, resonance_cycles=3)

    assert forecast.thread_count == 2
    assert 0.0 <= forecast.pulse_score <= 1.0
    assert 0.0 <= forecast.coherence_index <= 1.0

    summary = render_horizon_map(forecast)
    assert "Pulse score" in summary
    assert "Aurora Thread" in summary


def test_render_horizon_map_handles_empty_forecast() -> None:
    horizon = LuminalHorizon()
    signal = HorizonSignal("Solo", luminosity=0.4, confidence=0.5)
    horizon.project([signal], resonance_cycles=1)

    empty_forecast_text = render_horizon_map(
        HorizonForecast(threads=(), pulse_score=0.0, coherence_index=0.0, narrative=())
    )

    assert "Invite new signals" in empty_forecast_text
