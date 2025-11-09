import math

from echo.quantum_flux_mapper import QuantumFluxMapper, SIGIL_ROTATION_MAP


def test_weave_sigil_updates_history():
    mapper = QuantumFluxMapper()
    bloch = (0.0, 0.0, 1.0)
    mapper.weave_sigil("⟁", bloch)
    assert any("⟁" in entry for entry in mapper.history)
    x, y, z = mapper.bloch_coordinates()
    assert math.isclose(x * x + y * y + z * z, 1.0, rel_tol=1e-6)


def test_weave_sigil_unknown_symbol_uses_default():
    mapper = QuantumFluxMapper()
    mapper.weave_sigil("?", (0.0, 1.0, 0.0))
    assert any("?" in entry for entry in mapper.history)


def test_sigil_rotation_catalog_contains_expected_symbols():
    for glyph in ["⟁", "ϟ", "♒", "➶", "✶", "⋆", "𖤐", "⚯", "⚡", "∞"]:
        assert glyph in SIGIL_ROTATION_MAP
