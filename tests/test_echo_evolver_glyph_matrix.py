"""Tests for the procedural glyph matrix helper."""

import pytest

from echo.evolver import EchoEvolver


EXPECTED_RING = [
    "🠐",
    "🠑",
    "🠒",
    "🠓",
    "🠔",
    "🠕",
    "🠖",
    "🠗",
    "🠘",
    "🠙",
    "🠚",
    "🠛",
    "🠜",
    "🠝",
    "🠞",
    "🠟",
    "⧻",
    "⨴",
    "⨀",
    "⨺",
]


def _expected_matrix(width: int, height: int) -> list[list[str]]:
    matrix: list[list[str]] = []
    ring_length = len(EXPECTED_RING)
    for row in range(height):
        start = row % ring_length
        matrix.append([EXPECTED_RING[(start + column) % ring_length] for column in range(width)])
    return matrix


def test_glyph_matrix_returns_default_square_grid():
    evolver = EchoEvolver()

    matrix = evolver.glyph_matrix()

    assert len(matrix) == 20
    assert all(len(row) == 20 for row in matrix)
    assert matrix[0] == EXPECTED_RING
    # Matrix should wrap through the glyph ring for subsequent rows.
    assert matrix[1][:4] == EXPECTED_RING[1:5]
    expected_last_row_start = EXPECTED_RING[-1:] + EXPECTED_RING[:3]
    assert matrix[-1][:4] == expected_last_row_start


def test_glyph_matrix_supports_rectangular_dimensions():
    evolver = EchoEvolver()

    matrix = evolver.glyph_matrix(width=6, height=3)

    assert matrix == _expected_matrix(6, 3)
    assert evolver.state.network_cache["glyph_matrix"] == matrix


def test_glyph_font_svg_renders_full_ring_and_logs_event():
    evolver = EchoEvolver()

    svg = evolver.glyph_font_svg()

    assert svg.startswith("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
    assert svg.count("<glyph ") == len(EXPECTED_RING)
    assert "<font id=\"EchoGlyphFont\"" in svg
    assert evolver.state.network_cache["glyph_font_svg"] == svg
    assert evolver.state.event_log[-1] == "Glyph font SVG generated (20 glyphs)"


def test_glyph_font_svg_accepts_custom_parameters():
    evolver = EchoEvolver()

    svg = evolver.glyph_font_svg(["A", "B"], font_id="CustomFont", units_per_em=512)

    assert svg.count("<glyph ") == 2
    assert "<font id=\"CustomFont\"" in svg
    assert "units-per-em=\"512\"" in svg


def test_glyph_font_svg_validates_inputs():
    evolver = EchoEvolver()

    with pytest.raises(ValueError):
        evolver.glyph_font_svg([])

    with pytest.raises(ValueError):
        evolver.glyph_font_svg(font_id="   ")


def test_glyph_matrix_rejects_invalid_dimensions():
    evolver = EchoEvolver()

    try:
        evolver.glyph_matrix(width=0)
    except ValueError as exc:
        assert "width" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected glyph_matrix to validate width")

    try:
        evolver.glyph_matrix(width=1, height=0)
    except ValueError as exc:
        assert "height" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected glyph_matrix to validate height")
