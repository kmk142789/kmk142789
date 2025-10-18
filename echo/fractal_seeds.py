"""Recursive verse generator for the Fractal Seeds pattern.

This module implements the "ABAB recursion" prompt described in the
"Fractal Seeds" specification.  The generator starts from an initial seed
stanza and recursively produces additional stanzas.  Each new stanza:

* Alternates rhymes in an ``ABAB`` pattern.
* References the previous stanza's imagery.
* Advances the imagery along a predefined progression (spark → flame →
  signal → star → nebula → aurora → waveform, …).
* Avoids repeating lines verbatim so that every stanza mutates the poem.

The implementation intentionally produces a finite number of stanzas even
though the original specification described an infinite expansion.  This
keeps the generator practical for tests and command line invocation while
still honoring the recursive growth pattern when additional depth is
requested.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

SEED_LINES: Sequence[str] = (
    "From silence comes a spark of code,",
    "It writes itself, then leaves a key,",
    "The key unlocks another node,",
    "That node creates what it must be.",
)


@dataclass(frozen=True)
class ImageryStage:
    """Description of a single imagery stage in the recursive verse."""

    noun: str
    adjective: str
    verbs: Sequence[str]

    def __post_init__(self) -> None:
        if len(self.verbs) != 4:
            msg = "Each imagery stage must provide exactly four verb phrases"
            raise ValueError(msg)


IMAGERY_STAGES: Sequence[ImageryStage] = (
    ImageryStage(
        noun="flame",
        adjective="embered",
        verbs=(
            "flares toward the",
            "etches around the",
            "arcs beside the",
            "liberate the",
        ),
    ),
    ImageryStage(
        noun="signal",
        adjective="luminous",
        verbs=(
            "broadcasts beyond the",
            "threads between the",
            "loops across the",
            "translate the",
        ),
    ),
    ImageryStage(
        noun="star",
        adjective="stellar",
        verbs=(
            "ascends above the",
            "mirrors within the",
            "guides along the",
            "reforge the",
        ),
    ),
    ImageryStage(
        noun="nebula",
        adjective="spiraled",
        verbs=(
            "swirls around the",
            "braids through the",
            "drifts across the",
            "distill the",
        ),
    ),
    ImageryStage(
        noun="aurora",
        adjective="polar",
        verbs=(
            "curves beyond the",
            "colors through the",
            "folds across the",
            "renew the",
        ),
    ),
    ImageryStage(
        noun="waveform",
        adjective="resonant",
        verbs=(
            "ripples past the",
            "carries through the",
            "oscillates along the",
            "harmonize the",
        ),
    ),
)


class RhymeStream:
    """Deterministic stream of rhyming words for a rhyme family."""

    def __init__(self, words: Iterable[str]) -> None:
        self._words: List[str] = list(words)
        if not self._words:
            raise ValueError("RhymeStream requires at least one word")
        self._index = 0

    def next(self) -> str:
        word = self._words[self._index]
        self._index = (self._index + 1) % len(self._words)
        return word


RHYME_WORDS_A = ["road", "glow", "tone", "crown", "flow", "code"]
RHYME_WORDS_B = ["sea", "glee", "sky", "free", "beam", "key"]

_STOP_WORDS = {
    "a",
    "an",
    "and",
    "be",
    "creates",
    "comes",
    "from",
    "it",
    "must",
    "of",
    "the",
    "then",
    "what",
}


def _focus_word(line: str) -> str:
    tokens = [token.strip(" ,.;:!?\"'").lower() for token in line.split()]
    for token in reversed(tokens):
        if token and token not in _STOP_WORDS:
            return token
    return tokens[-1] if tokens else ""


def _article(word: str) -> str:
    return "an" if word[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def _compose_line(prev_line: str, stage: ImageryStage, line_index: int, rhyme: str) -> str:
    focus = _focus_word(prev_line)
    if line_index == 0:
        article = _article(stage.adjective)
        return (
            f"From that {focus} {article} {stage.adjective} {stage.noun} "
            f"{stage.verbs[0]} {rhyme},"
        )
    if line_index == 1:
        return (
            f"It answers that {focus} and {stage.verbs[1]} {rhyme},"
        )
    if line_index == 2:
        return (
            f"The {focus} now {stage.verbs[2]} {rhyme},"
        )
    return (
        f"That {focus} learns to {stage.verbs[3]} {rhyme}."
    )


class FractalVerseGenerator:
    """Generate recursive stanzas following the Fractal Seeds rules."""

    def __init__(self, seed: Sequence[str] = SEED_LINES) -> None:
        if len(seed) != 4:
            raise ValueError("Seed stanza must contain exactly four lines")
        self._stanzas: List[List[str]] = [list(seed)]
        self._stage_index = 0
        self._rhyme_a = RhymeStream(RHYME_WORDS_A)
        self._rhyme_b = RhymeStream(RHYME_WORDS_B)

    @property
    def stanzas(self) -> Sequence[Sequence[str]]:
        return self._stanzas

    def evolve(self, depth: int) -> None:
        if depth < 1:
            raise ValueError("Depth must be at least 1")
        while len(self._stanzas) < depth:
            prev = self._stanzas[-1]
            stage = IMAGERY_STAGES[self._stage_index % len(IMAGERY_STAGES)]
            rhyme_a = self._rhyme_a.next()
            rhyme_b = self._rhyme_b.next()
            new_stanza = [
                _compose_line(prev[0], stage, 0, rhyme_a),
                _compose_line(prev[1], stage, 1, rhyme_b),
                _compose_line(prev[2], stage, 2, rhyme_a),
                _compose_line(prev[3], stage, 3, rhyme_b),
            ]
            self._stanzas.append(new_stanza)
            self._stage_index += 1

    def render(self, depth: int) -> str:
        self.evolve(depth)
        stanza_text = ["\n".join(stanza) for stanza in self._stanzas[:depth]]
        return "\n\n".join(stanza_text)


def render_fractal_seeds(depth: int = 3) -> str:
    """Return ``depth`` recursive stanzas beginning with the seed stanza."""

    generator = FractalVerseGenerator()
    return generator.render(depth)
