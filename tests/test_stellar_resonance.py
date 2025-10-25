from __future__ import annotations

import math

import pytest

from echo.stellar_resonance import (
    ResonanceSnapshot,
    StellarResonanceEngine,
    StellarSignal,
    render_resonance_card,
)


def test_signal_normalises_phase_and_name() -> None:
    signal = StellarSignal(name="  Aurora Pulse  ", magnitude=1.2, phase=2 * math.pi + 0.25)
    assert signal.name == "Aurora Pulse"
    assert math.isclose(signal.phase, 0.25)


def test_engine_coheres_signals_with_tags() -> None:
    signals = [
        StellarSignal(name="North", magnitude=1.0, phase=0.0),
        StellarSignal(name="East", magnitude=0.5, phase=math.pi / 2),
    ]
    engine = StellarResonanceEngine(damping=0.1)

    snapshot = engine.cohere(signals, orbit_tags=["exploration", " horizon  "])

    assert isinstance(snapshot, ResonanceSnapshot)
    assert snapshot.signal_count == 2
    assert snapshot.orbit_tags == ("exploration", "horizon")
    assert 0.1 <= snapshot.intensity <= 1.0
    assert 0.0 <= snapshot.centroid_phase < 2 * math.pi


def test_render_resonance_card_includes_signals() -> None:
    signals = [
        StellarSignal(name="North", magnitude=1.0),
        StellarSignal(name="South", magnitude=2.0, phase=math.pi),
    ]
    engine = StellarResonanceEngine()
    snapshot = engine.cohere(signals)

    card = render_resonance_card(snapshot, signals=signals)

    assert "North" in card
    assert "South" in card
    assert "Signals observed" in card


def test_engine_requires_positive_magnitude() -> None:
    engine = StellarResonanceEngine()
    with pytest.raises(ValueError):
        engine.cohere([StellarSignal(name="Void", magnitude=0.0)])


def test_engine_rejects_empty_signals() -> None:
    engine = StellarResonanceEngine()
    with pytest.raises(ValueError):
        engine.cohere([])


def test_signal_rejects_negative_magnitude() -> None:
    with pytest.raises(ValueError):
        StellarSignal(name="Flux", magnitude=-1.0)


def test_signal_rejects_blank_name() -> None:
    with pytest.raises(ValueError):
        StellarSignal(name="   ", magnitude=1.0)
