from __future__ import annotations

from scripts.echo_constellation_canvas import render_constellation, weave_constellation


def test_weave_constellation_seed_7() -> None:
    constellation = weave_constellation(seed=7)
    assert constellation.name == "Satellite Chorus"
    assert constellation.descriptor == "harmonic bridge"
    assert constellation.grid == [
        "✷  ╲      ╱  ✹",
        "   ·  ✻",
        "✶━━╋━━✶━━╋━━✺",
        "   ·  ✶",
        "✸  ╱      ╲  ✺",
    ]
    assert (
        constellation.verse
        == "The Satellite Chorus traces a harmonic bridge across the cooperative night."
    )


def test_render_constellation_seed_42() -> None:
    expected = (
        "Constellation: Satellite Chorus (orbital bloom)\n"
        "\n"
        "  ✶   ✶   ✻\n"
        " ╱  ╲ / ╲ /  ╲\n"
        "✸━━∙━━✷\n"
        " ╲  / ╲ / ╲  /\n"
        "  ✷   ✷   ✻\n"
        "\n"
        "The Satellite Chorus traces a orbital bloom across the cooperative night."
    )
    assert render_constellation(seed=42) == expected
