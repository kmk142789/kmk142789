"""Tests for :mod:`echo.stellar_story_forge`."""
from __future__ import annotations

import pytest

from echo.stellar_story_forge import StorySpark, StellarStoryForge


def test_weave_produces_expected_fragments() -> None:
    sparks = [
        StorySpark(
            theme="Aurora Archive",
            mood="hopeful",
            resonance=0.78,
            constellations=("ice halo", "dawn filament"),
        )
    ]

    forge = StellarStoryForge(base_luminosity=0.35)
    weave = forge.weave(sparks, passages=2, cadence="heartbeat")

    assert weave.fragment_count == 2
    assert weave.cadence == "heartbeat"
    assert weave.orbit_summary == ("Aurora Archive::hopeful",)
    assert all(fragment.tone == "hopeful" for fragment in weave.fragments)

    second = forge.weave(sparks, passages=2, cadence="heartbeat")
    assert [frag.narrative for frag in second.fragments] == [frag.narrative for frag in weave.fragments]
    assert [frag.luminosity for frag in second.fragments] == [frag.luminosity for frag in weave.fragments]


def test_weave_input_validation() -> None:
    forge = StellarStoryForge()

    with pytest.raises(ValueError):
        forge.weave([], passages=1)

    spark = StorySpark(theme="Orbit", mood="calm", resonance=0.1)
    with pytest.raises(ValueError):
        forge.weave([spark], passages=0)


@pytest.mark.parametrize(
    "theme, mood",
    [
        ("", "serene"),
        ("   ", "serene"),
        ("Aurora", ""),
        ("Aurora", "   "),
    ],
)
def test_story_spark_requires_theme_and_mood(theme: str, mood: str) -> None:
    with pytest.raises(ValueError):
        StorySpark(theme=theme, mood=mood)
