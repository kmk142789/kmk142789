import re
from echo.stellar_echo import (
    EchoVerse,
    IMAGERY_LIBRARY,
    compose_stellar_echo,
    render_composition,
)


def test_compose_uses_default_cycle_when_invalid():
    verses = compose_stellar_echo("   ", cycles=0)
    assert len(verses) == 1
    assert verses[0].theme == "Silent Resonance"


def test_compose_generates_expected_imagery_rotation():
    verses = compose_stellar_echo("galactic memory", cycles=len(IMAGERY_LIBRARY) + 2)
    imagery_sequence = [verse.imagery for verse in verses]
    expected = IMAGERY_LIBRARY + IMAGERY_LIBRARY[:2]
    assert imagery_sequence == expected


def test_render_composition_includes_timestamp_format():
    verse = EchoVerse(cycle=1, theme="Pulse", imagery="Sample imagery")
    rendered = render_composition([verse])
    assert re.match(r"Cycle 01 \| Pulse \| Sample imagery \| \d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z", rendered)
