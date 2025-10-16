"""Tests for the procedural glyph matrix helper."""

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
