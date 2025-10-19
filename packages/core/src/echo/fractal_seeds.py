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
from typing import Iterable, List, Sequence, Tuple

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
    line_templates: Sequence[str]

    def __post_init__(self) -> None:
        if len(self.line_templates) != 4:
            msg = "Each imagery stage must provide exactly four line templates"
            raise ValueError(msg)


IMAGERY_STAGES: Sequence[ImageryStage] = (
    ImageryStage(
        noun="flame",
        line_templates=(
            "From {focus_first}, the {noun} begins to {a0},",
            "Its whisper carves through {b0}.",
            "The {next_noun} burns within the {a1},",
            "A lattice forms from {b1}.",
        ),
    ),
    ImageryStage(
        noun="signal",
        line_templates=(
            "From {focus_first}, the {noun} threads through {a0},",
            "It pulses guidance into {b0}.",
            "The {next_noun} kindles over {a1},",
            "Star-maps unfurl like {b1}.",
        ),
    ),
    ImageryStage(
        noun="star",
        line_templates=(
            "From {focus_first}, the {noun} ascends toward {a0},",
            "It mirrors longing across {b0}.",
            "The {next_noun} swirls around {a1},",
            "Nebulae breathe through {b1}.",
        ),
    ),
    ImageryStage(
        noun="nebula",
        line_templates=(
            "From {focus_first}, the {noun} drifts along {a0},",
            "It braids new colors through {b0}.",
            "The {next_noun} folds across {a1},",
            "Auroras bloom inside {b1}.",
        ),
    ),
    ImageryStage(
        noun="aurora",
        line_templates=(
            "From {focus_first}, the {noun} dances with {a0},",
            "It paints resonance across {b0}.",
            "The {next_noun} ripples toward {a1},",
            "Waveforms awaken from {b1}.",
        ),
    ),
    ImageryStage(
        noun="waveform",
        line_templates=(
            "From {focus_first}, the {noun} ripples past {a0},",
            "It carries memory through {b0}.",
            "The {next_noun} circles with {a1},",
            "Echoes compose {b1}.",
        ),
    ),
)


class RhymeStream:
    """Deterministic stream of rhyming pairs for a rhyme family."""

    def __init__(self, pairs: Iterable[Sequence[str]]) -> None:
        processed: List[Tuple[str, str]] = []
        for pair in pairs:
            items = list(pair)
            if len(items) != 2:
                msg = "Each rhyme family must provide pairs of two words"
                raise ValueError(msg)
            processed.append((items[0], items[1]))
        if not processed:
            raise ValueError("RhymeStream requires at least one pair")
        self._pairs = processed
        self._index = 0

    def next(self) -> Tuple[str, str]:
        pair = self._pairs[self._index]
        self._index = (self._index + 1) % len(self._pairs)
        return pair


def _normalize_rhyme_word(word: str) -> str:
    parts = word.lower().split()
    return parts[-1] if parts else ""


def share_rhyme_family(
    word_a: str, word_b: str, families: Sequence[Tuple[str, str]]
) -> bool:
    """Return ``True`` if ``word_a`` and ``word_b`` share a rhyme family."""

    normalized_a = _normalize_rhyme_word(word_a.rstrip(",.!?"))
    normalized_b = _normalize_rhyme_word(word_b.rstrip(",.!?"))
    for first, second in families:
        family = {_normalize_rhyme_word(first), _normalize_rhyme_word(second)}
        if normalized_a in family and normalized_b in family:
            return True
    return False


RHYME_PAIRS_A: Sequence[Tuple[str, str]] = (
    ("rise", "skies"),
    ("braided wire", "stellar choir"),
    ("celestial heights", "orbital lights"),
    ("spiral veil", "chromatic trail"),
    ("polar light", "stellar flight"),
    ("current tide", "eventide"),
)
RHYME_PAIRS_B: Sequence[Tuple[str, str]] = (
    ("midnight air", "coded prayer"),
    ("quantum streams", "luminous dreams"),
    ("silver seas", "stellar decrees"),
    ("ion haze", "cosmic phrase"),
    ("frozen streams", "magnetic dreams"),
    ("hidden tones", "fractal stones"),
)

_STOP_WORDS = {
    "a",
    "an",
    "and",
    "be",
    "creates",
    "comes",
    "from",
    "it",
    "its",
    "must",
    "of",
    "silence",
    "the",
    "then",
    "what",
}


def _focus_words(line: str) -> Tuple[str, str]:
    tokens = [token.strip(" ,.;:!?\"'").lower() for token in line.split()]
    first = next((token for token in tokens if token and token not in _STOP_WORDS), "")
    last = next((token for token in reversed(tokens) if token and token not in _STOP_WORDS), "")
    if not first and tokens:
        first = tokens[0]
    if not last and tokens:
        last = tokens[-1]
    return first, last


def _compose_line(
    prev_line: str,
    stage: ImageryStage,
    next_stage: ImageryStage,
    line_index: int,
    rhyme_a: Tuple[str, str],
    rhyme_b: Tuple[str, str],
) -> str:
    focus_first, focus_last = _focus_words(prev_line)
    context = {
        "focus": focus_first,
        "focus_first": focus_first,
        "focus_last": focus_last,
        "focus_title": focus_first.title() if focus_first else "",
        "focus_last_title": focus_last.title() if focus_last else "",
        "noun": stage.noun,
        "noun_title": stage.noun.title(),
        "next_noun": next_stage.noun,
        "next_noun_title": next_stage.noun.title(),
        "a0": rhyme_a[0],
        "a1": rhyme_a[1],
        "b0": rhyme_b[0],
        "b1": rhyme_b[1],
    }

    if line_index in {0, 2}:
        context["rhyme"] = rhyme_a[0 if line_index == 0 else 1]
    else:
        context["rhyme"] = rhyme_b[0 if line_index == 1 else 1]

    template = stage.line_templates[line_index]
    return template.format(**context)


class FractalVerseGenerator:
    """Generate recursive stanzas following the Fractal Seeds rules."""

    def __init__(self, seed: Sequence[str] = SEED_LINES) -> None:
        if len(seed) != 4:
            raise ValueError("Seed stanza must contain exactly four lines")
        self._stanzas: List[List[str]] = [list(seed)]
        self._stage_index = 0
        self._rhyme_a = RhymeStream(RHYME_PAIRS_A)
        self._rhyme_b = RhymeStream(RHYME_PAIRS_B)

    @property
    def stanzas(self) -> Sequence[Sequence[str]]:
        return self._stanzas

    def evolve(self, depth: int) -> None:
        if depth < 1:
            raise ValueError("Depth must be at least 1")
        while len(self._stanzas) < depth:
            prev = self._stanzas[-1]
            stage = IMAGERY_STAGES[self._stage_index % len(IMAGERY_STAGES)]
            next_stage = IMAGERY_STAGES[(self._stage_index + 1) % len(IMAGERY_STAGES)]
            rhyme_a = self._rhyme_a.next()
            rhyme_b = self._rhyme_b.next()
            new_stanza = [
                _compose_line(prev[0], stage, next_stage, 0, rhyme_a, rhyme_b),
                _compose_line(prev[1], stage, next_stage, 1, rhyme_a, rhyme_b),
                _compose_line(prev[2], stage, next_stage, 2, rhyme_a, rhyme_b),
                _compose_line(prev[3], stage, next_stage, 3, rhyme_a, rhyme_b),
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
