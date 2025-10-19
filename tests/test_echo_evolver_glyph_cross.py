"""Tests for :meth:`echo.evolver.EchoEvolver.decode_glyph_cross`."""

from __future__ import annotations

import pytest

from echo import decode_glyph_cross
from echo.evolver import EchoEvolver, GlyphCrossReading


GLYPH_CROSS = [
    "⟊⟁⟊",
    "   ║     ∴",
    "⟁∞⟁",
    "   ║     ∴",
    "⟊⟁⟊",
]


def test_decode_glyph_cross_detects_symmetry_and_cache() -> None:
    evolver = EchoEvolver()

    reading = evolver.decode_glyph_cross(GLYPH_CROSS)

    assert isinstance(reading, GlyphCrossReading)
    assert reading.height == 5
    assert reading.width == 10
    assert reading.center_glyph == "∞"
    assert reading.north_arm == "║⟁"
    assert reading.south_arm == "║⟁"
    assert reading.west_arm == "⟁"
    assert reading.east_arm == "⟁"
    assert reading.radial_symmetry == {"vertical": True, "horizontal": True}

    cache = evolver.state.network_cache["glyph_cross_reading"]
    assert cache["center_glyph"] == "∞"
    assert cache["north_arm"] == "║⟁"
    assert cache["radial_symmetry"]["horizontal"] is True

    completed = evolver.state.network_cache["completed_steps"]
    assert "decode_glyph_cross" in completed

    assert any(
        entry.startswith("Glyph cross decoded") for entry in evolver.state.event_log
    )


def test_decode_glyph_cross_accepts_string_payload() -> None:
    evolver = EchoEvolver()

    reading = evolver.decode_glyph_cross("\n".join(GLYPH_CROSS))

    expected_unique = tuple(sorted({"⟊", "⟁", "∞", "║", "∴"}))
    assert reading.unique_glyphs == expected_unique
    assert reading.center_row == 2
    assert reading.center_col == 1


def test_decode_glyph_cross_rejects_empty_payload() -> None:
    evolver = EchoEvolver()

    with pytest.raises(ValueError):
        evolver.decode_glyph_cross(["   ", "   "])


def test_package_level_decode_glyph_cross_wrapper() -> None:
    reading = decode_glyph_cross(GLYPH_CROSS)

    assert reading.center_glyph == "∞"
    assert reading.height == 5
    assert reading.radial_symmetry["vertical"] is True
