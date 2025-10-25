"""Tests for the creative radiance utilities."""
from __future__ import annotations

import pytest

from echo.creative_radiance import RadianceSynthesizer, RadiantIdea, spark_radiance


def test_radiant_idea_validates_and_computes_spectral_index() -> None:
    idea = RadiantIdea(theme=" Orbital lighthouse ", luminosity=0.7, motifs=("beacon", "hope", "beacon"))
    assert idea.theme == "Orbital lighthouse"
    assert idea.motifs == ("beacon", "hope")
    assert idea.spectral_index == pytest.approx(0.79, rel=1e-6)


@pytest.mark.parametrize(
    "currents,expected",
    [
        (None, [0.52, 0.52, 0.52]),
        ([5.0, 7.0, 9.0], [0.0, pytest.approx(0.5), 1.0]),
        ([0.3, 0.3, 0.3], [0.3, 0.3, 0.3]),
    ],
)
def test_radiance_synthesizer_calibrate_normalises(currents, expected) -> None:
    glimpses = ["Signal A", "Signal B", "Signal C"]
    synthesizer = RadianceSynthesizer()
    ideas = synthesizer.calibrate(glimpses, currents=currents)
    assert [idea.luminosity for idea in ideas] == expected


def test_compose_chorus_highlights_top_ideas() -> None:
    synthesizer = RadianceSynthesizer()
    ideas = synthesizer.calibrate(
        ["Signal A", "Signal B", "Signal C"],
        currents=[0.2, 0.6, 0.9],
        motifs=[("whisper",), ("beam", "pulse"), ()],
    )
    chorus = synthesizer.compose_chorus(ideas)
    assert chorus == "Radiant chorus: Signal C; Signal B (beam, pulse); Signal A (whisper)"


@pytest.mark.parametrize(
    "accent,expected_prefix",
    [(None, "Radiant chorus"), ("Luminous", "Luminous :: Radiant chorus")],
)
def test_spark_radiance_returns_summary(accent, expected_prefix) -> None:
    summary = spark_radiance(["Dream seed", "Orbit drift"], accent=accent)
    assert summary.startswith(expected_prefix)


def test_invalid_inputs_raise_errors() -> None:
    synthesizer = RadianceSynthesizer()
    with pytest.raises(ValueError):
        synthesizer.calibrate([])
    with pytest.raises(ValueError):
        synthesizer.calibrate(["one"], currents=[0.1, 0.2])
    with pytest.raises(ValueError):
        synthesizer.compose_chorus([])

    with pytest.raises(ValueError):
        RadianceSynthesizer(base_luminosity=-0.1)
    with pytest.raises(ValueError):
        RadiantIdea(theme="", luminosity=0.5)
    with pytest.raises(ValueError):
        RadiantIdea(theme="Spark", luminosity=1.5)
