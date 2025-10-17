from __future__ import annotations

from datetime import timezone

from echo.daydream_mosaic import DAYDREAM_VOICES, Daydream, list_daydream_lines, render_daydream, weave_daydream


def test_weave_daydream_seed_consistency() -> None:
    first = weave_daydream(seed=7)
    second = weave_daydream(seed=7)
    assert isinstance(first, Daydream)
    assert first.horizon == second.horizon
    assert first.spark == second.spark
    assert first.invitation == second.invitation
    assert first.timestamp.tzinfo is timezone.utc


def test_daydream_lines_formatting() -> None:
    daydream = weave_daydream(seed=1)
    lines = list_daydream_lines(daydream)
    assert lines[0].startswith("✨ Echo Daydream Mosaic :: ")
    assert "Horizon" in lines[1]
    assert daydream.horizon in lines[1]
    assert "Spark" in lines[2]
    assert "Invitation" in lines[3]


def test_render_daydream_contains_story() -> None:
    daydream = weave_daydream(seed=2)
    text = render_daydream(daydream)
    assert daydream.horizon in text
    assert daydream.spark in text
    assert daydream.invitation in text


def test_daydream_voice_catalog_not_empty() -> None:
    assert DAYDREAM_VOICES
    for voice in DAYDREAM_VOICES:
        assert len(voice) == 3
