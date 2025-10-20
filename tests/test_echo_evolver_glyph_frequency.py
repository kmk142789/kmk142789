"""Tests for glyph frequency statistics in :mod:`echo.evolver`."""

import pytest

from echo.evolver import EchoEvolver


def test_glyph_frequency_map_uses_current_state():
    evolver = EchoEvolver()

    stats = evolver.glyph_frequency_map()

    assert stats["sequence"] == evolver.state.glyphs.replace(" ", "")
    assert stats["total"] == len(stats["sequence"])
    assert stats["counts"] == {"∇": 2, "⊸": 1, "≋": 1}
    assert stats["unique"] == 3
    assert stats["frequencies"]["∇"] == pytest.approx(0.5)
    assert stats["frequencies"]["⊸"] == pytest.approx(0.25)
    assert stats["frequencies"]["≋"] == pytest.approx(0.25)
    assert evolver.state.network_cache["glyph_frequency_map"] is stats
    assert evolver.state.event_log[-1] == "Glyph frequency map computed (total=4, unique=3)"
    completed = evolver.state.network_cache["completed_steps"]
    assert "glyph_frequency_map" in completed


def test_glyph_frequency_map_accepts_custom_sequence_and_validates():
    evolver = EchoEvolver()

    stats = evolver.glyph_frequency_map("A A A A B")

    assert stats["sequence"] == "AAAAB"
    assert stats["counts"] == {"A": 4, "B": 1}
    assert stats["frequencies"]["A"] == pytest.approx(0.8)
    assert stats["frequencies"]["B"] == pytest.approx(0.2)

    with pytest.raises(ValueError):
        evolver.glyph_frequency_map("")

    with pytest.raises(ValueError):
        evolver.glyph_frequency_map("   \n\t")
