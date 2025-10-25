from __future__ import annotations

import pytest

from echo.innovation_wave import (
    InnovationSpark,
    InnovationWave,
    InnovationWaveReport,
    render_wave_map,
)


def test_innovation_spark_normalises_fields() -> None:
    spark = InnovationSpark(theme="  Galactic Leap  ", momentum=1.2, vectors=("alpha", "", " beta "))
    assert spark.theme == "Galactic Leap"
    assert spark.momentum == pytest.approx(1.0)
    assert spark.vectors == ("alpha", "beta")


def test_innovation_wave_propagate_generates_bridges() -> None:
    sparks = (
        InnovationSpark("Signal", 0.9, vectors=("aurora",)),
        InnovationSpark("Echo", 0.3),
    )
    wave = InnovationWave(base_resonance=0.2, weave_gain=0.1)

    report = wave.propagate(sparks, arcs=2, weaving=["Pulse Drift"])

    assert report.bridge_count == 4
    assert report.orbit_summary == ("Signal", "Echo")
    assert 0.2 <= report.average_resonance <= 1.0

    map_text = render_wave_map(report)
    assert "1. Signal ↠ arc 1" in map_text
    assert "Pulse Drift" in map_text


def test_innovation_wave_validation() -> None:
    wave = InnovationWave()
    with pytest.raises(ValueError):
        wave.propagate((), arcs=2)
    with pytest.raises(ValueError):
        wave.propagate((InnovationSpark("Spark", 0.5),), arcs=0)


def test_render_wave_map_with_no_bridges() -> None:
    empty_message = render_wave_map(
        InnovationWaveReport(bridges=(), average_resonance=0.0, orbit_summary=())
    )
    assert "No bridges" in empty_message
