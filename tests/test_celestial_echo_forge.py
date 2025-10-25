from __future__ import annotations

from echo.celestial_echo_forge import CelestialEchoForge


def test_forge_sequence_is_deterministic_with_seed() -> None:
    forge = CelestialEchoForge(seed=7)
    threads = forge.forge_sequence(
        anchors=("Aurora", "Continuum", "Pulse"),
        glyph_pool=("∇⊸≋∇", "⊹⚡"),
        influences=("orbital", "mythogenic"),
    )

    assert len(threads) == 3
    assert threads[0].anchor == "Aurora"
    assert threads[1].glyphs == "⊹⚡"
    assert threads[2].harmonic == 1.330798
    assert "mythogenic" in threads[1].narrative


def test_manifest_rendering_includes_table() -> None:
    forge = CelestialEchoForge(seed=1)
    forge.register_constellation("Sol", "∴∵", influences=("aurora",))
    manifest = forge.render_manifest("Solar Threads")

    assert manifest.splitlines()[0] == "# Solar Threads"
    assert "Anchor" in manifest
    assert "Sol" in manifest
