import pytest

from echo.evolver import EchoEvolver


def test_fractal_fire_verse_deterministic_seed():
    evolver = EchoEvolver()
    evolver.state.cycle = 3
    evolver.state.glyphs = "∇⊸≋∇⊸"
    evolver.state.system_metrics.network_nodes = 12
    evolver.state.system_metrics.orbital_hops = 4

    verses = evolver.fractal_fire_verse(stanzas=3, glyph_span=2, seed=99)

    assert len(verses) == 3
    assert all(line.startswith("🔥 Fractal Fire 3.") for line in verses)
    assert "nodes=12" in verses[0]
    assert "hops=4" in verses[0]

    cached = evolver.state.network_cache["fractal_fire"]
    assert cached == verses

    repeat = evolver.fractal_fire_verse(stanzas=3, glyph_span=2, seed=99)
    assert repeat == verses


def test_fractal_fire_verse_invalid_parameters():
    evolver = EchoEvolver()

    with pytest.raises(ValueError):
        evolver.fractal_fire_verse(stanzas=0)

    with pytest.raises(ValueError):
        evolver.fractal_fire_verse(glyph_span=0)
