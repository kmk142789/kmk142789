from __future__ import annotations

from echo.fractal_seeds import (
    FractalVerseGenerator,
    RHYME_PAIRS_A,
    RHYME_PAIRS_B,
    SEED_LINES,
    render_fractal_seeds,
    share_rhyme_family,
)


def _last_word(line: str) -> str:
    return line.rstrip(",.?!").split()[-1]


def test_render_includes_seed_and_evolution() -> None:
    poem = render_fractal_seeds(depth=2)
    stanzas = [stanza.splitlines() for stanza in poem.split("\n\n")]
    assert stanzas[0] == list(SEED_LINES)

    evolved = stanzas[1]
    assert evolved == [
        "From spark, the flame begins to rise,",
        "Its whisper carves through midnight air.",
        "The signal burns within the skies,",
        "A lattice forms from coded prayer.",
    ]


def test_abab_rhyme_pattern_is_preserved() -> None:
    generator = FractalVerseGenerator()
    generator.evolve(depth=4)
    for stanza in generator.stanzas[1:4]:
        last_a0 = _last_word(stanza[0])
        last_a1 = _last_word(stanza[2])
        last_b0 = _last_word(stanza[1])
        last_b1 = _last_word(stanza[3])
        assert share_rhyme_family(last_a0, last_a1, RHYME_PAIRS_A)
        assert share_rhyme_family(last_b0, last_b1, RHYME_PAIRS_B)


def test_each_stanza_mutates_previous() -> None:
    generator = FractalVerseGenerator()
    generator.evolve(depth=3)
    previous = generator.stanzas[0]
    for stanza in generator.stanzas[1:3]:
        for line_prev, line_next in zip(previous, stanza):
            assert line_prev != line_next
        previous = stanza
