"""Tests for the imagination weaving utilities."""

from __future__ import annotations

import pytest

from echo.inspiration import weave_imagination_sequence


def test_weave_imagination_sequence_deterministic() -> None:
    sequence = weave_imagination_sequence("Eden", horizons=3, intensity=0.7, rng_seed=11)

    assert sequence.theme == "Eden"
    assert sequence.seed == 11
    assert [phase.index for phase in sequence.phases] == [1, 2, 3]
    assert [phase.resonance for phase in sequence.phases] == [0.7, 0.85, 1.0]
    assert sequence.phases[0].spark == (
        "Breathe an orbit around Eden soft thunder to guide tomorrow"
    )
    assert sequence.phases[1].vector == "Refract Eden's promise through the luminous archive"
    assert sequence.phases[2].spark.endswith("under shared skies")


def test_weave_imagination_sequence_markdown_export() -> None:
    sequence = weave_imagination_sequence("Eden", horizons=2, intensity=0.9, rng_seed=5)

    markdown = sequence.to_markdown()

    assert markdown.startswith("# Imagination sequence for Eden\n")
    assert "- resonance: 0.90" in markdown
    assert markdown.endswith("\n")
    assert "> seeded with 5" in markdown


def test_weave_imagination_sequence_validates_inputs() -> None:
    with pytest.raises(ValueError):
        weave_imagination_sequence("", horizons=0)
    with pytest.raises(ValueError):
        weave_imagination_sequence("Echo", horizons=2, intensity=0.0)
    with pytest.raises(ValueError):
        weave_imagination_sequence("Echo", horizons=2, intensity=1.2)
