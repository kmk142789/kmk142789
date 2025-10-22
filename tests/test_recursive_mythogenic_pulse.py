"""Tests for :mod:`echo.recursive_mythogenic_pulse`."""
from __future__ import annotations

import pytest

from echo.recursive_mythogenic_pulse import (
    compose_voyage,
    generate_ascii_spiral,
    list_voyage_lines,
)


def test_compose_voyage_seed_determinism():
    voyage = compose_voyage(seed=7, recursion_level=3)

    assert voyage.glyph_orbit in {"∇⊸≋", "⊹∞⋰", "✶∴✶", "⟡⟳⟡", "☌⋱☌"}
    assert voyage.recursion_level == 3
    assert len(voyage.resonance) == 4
    assert all(" // " in thread for thread in voyage.resonance)

    lines = list_voyage_lines(voyage)
    assert lines[0].startswith("🔥 Mythogenic Pulse Voyage :: ")
    assert "Recursion Level" in lines[2]


def test_generate_ascii_spiral_layout():
    voyage = compose_voyage(seed=3, recursion_level=2)
    spiral = generate_ascii_spiral(voyage, radius=3)

    rows = spiral.splitlines()
    assert len(rows) == 7
    assert all(len(row) == 7 for row in rows)
    assert any(char.strip() for row in rows for char in row)


def test_compose_voyage_invalid_recursion_level():
    with pytest.raises(ValueError):
        compose_voyage(recursion_level=0)


def test_generate_ascii_spiral_invalid_radius():
    voyage = compose_voyage(seed=1)
    with pytest.raises(ValueError):
        generate_ascii_spiral(voyage, radius=1)
