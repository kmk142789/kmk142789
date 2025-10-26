"""Tests for the spectral canvas generator."""

from __future__ import annotations

import numpy as np
import pytest

pd = pytest.importorskip("pandas")

from echo.spectral_canvas import SpectralCanvas, generate_palette


def test_generate_palette_is_deterministic() -> None:
    seed = "mythic-seed"
    first = generate_palette(seed, size=3)
    second = generate_palette(seed, size=3)
    assert [color.to_hex() for color in first] == [color.to_hex() for color in second]


def test_generate_palette_rejects_invalid_size() -> None:
    with pytest.raises(ValueError, match="Palette size"):
        generate_palette("seed", size=0)


def test_canvas_render_matrix_shape_and_range() -> None:
    canvas = SpectralCanvas(width=4, height=3, seed="aurora", layers=("alpha", "beta"))
    matrix = canvas.render_matrix()
    assert matrix.shape == (3, 4, 3)
    assert np.all(matrix >= 0.0) and np.all(matrix <= 1.0)
    np.testing.assert_allclose(matrix, canvas.render_matrix())


def test_canvas_dataframe_matches_matrix() -> None:
    canvas = SpectralCanvas(width=2, height=2, seed="atlas", layers=("delta",))
    matrix = canvas.render_matrix()
    frame = canvas.as_dataframe()
    assert isinstance(frame, pd.DataFrame)
    assert frame.shape == (4, 5)
    assert set(frame.columns) == {"x", "y", "red", "green", "blue"}
    rebuilt = frame.sort_values(["y", "x"]).reset_index(drop=True)
    expected = matrix.reshape(-1, 3)
    np.testing.assert_allclose(rebuilt[["red", "green", "blue"]].to_numpy(), expected)


def test_canvas_description_contains_expected_rows() -> None:
    canvas = SpectralCanvas(width=3, height=2, seed="echo", layers=())
    table = canvas.describe()
    assert table.title == "Spectral Canvas – echo"
    assert [column.header for column in table.columns] == ["Channel", "Tone", "Range"]
    assert len(table.rows) == 3
    assert all(isinstance(row.cells[1], str) for row in table.rows)

