from __future__ import annotations

from echo.ritual_registry import compose_ritual, list_ritual_lines, render_ritual


def test_compose_ritual_seed_consistency():
    ritual = compose_ritual(seed=7)

    assert ritual.focus == "Bridge Sync"
    assert ritual.cadence == "resonant tones weave between paired whiteboards"
    assert ritual.anchor == "pair off and trade one sentence updates in under a minute"
    assert ritual.closing == "note one promise to revisit in the next check-in"

    lines = list_ritual_lines(ritual)
    assert lines[0].startswith("🕯️ Echo Ritual Registry :: ")
    assert "Focus" in lines[1]
    assert ritual.anchor in lines[3]

    rendered = render_ritual(ritual)
    flattened = rendered.replace("\n", " ")
    assert ritual.focus in flattened
    assert ritual.anchor in flattened
    assert ritual.closing in flattened
