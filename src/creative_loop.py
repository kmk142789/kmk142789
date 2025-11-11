"""Creative loop generator for playful improvisations.

This module creates short clusters of statements that orbit around a motif.
Each loop is designed to feel rhythmic, blending observational language with
imaginative declarations.  The module can be imported as a library or used
from the command line to print a loop to stdout.

Version two deepens the internal representation by modelling rhythm patterns
and diagnostics.  :class:`LoopRhythm` instances capture syncopation accents and
tempo variations that shape each generated sentence.  The accompanying
:class:`LoopDiagnostics` records metadata that can be inspected by external
systems to understand which narrative voices and fragments were emphasised.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
import random
from typing import Dict, Iterable, List, Tuple


@dataclass
class LoopSeed:
    """Parameters that describe the creative loop we want to generate."""

    motif: str
    fragments: Iterable[str] = field(default_factory=list)
    tempo: str = "andante"
    pulses: int = 3
    seed: int | None = None

    def __post_init__(self) -> None:
        self.fragments = list(self.fragments)
        if self.pulses < 1:
            raise ValueError("pulses must be positive")


@dataclass
class LoopRhythm:
    """Encapsulate syncopation, tempo variance, and pulse metadata."""

    tempo: str
    pulses: int
    accents: List[int]
    dynamic_tempi: List[str]

    def accent_for(self, index: int) -> int:
        return self.accents[index % len(self.accents)]

    def tempo_for(self, index: int) -> str:
        return self.dynamic_tempi[index % len(self.dynamic_tempi)]


@dataclass
class LoopDiagnostics:
    """Record metadata about the generated loop for downstream tooling."""

    voices: Counter[str] = field(default_factory=Counter)
    fragments: Counter[str] = field(default_factory=Counter)
    accents: List[int] = field(default_factory=list)

    def register(self, voice: str, fragment: str | None, accent: int) -> None:
        self.voices[voice] += 1
        if fragment:
            self.fragments[fragment] += 1
        self.accents.append(accent)

    def render_report(self) -> str:
        ordered_voices = ", ".join(f"{voice}:{count}" for voice, count in self.voices.items())
        ordered_fragments = ", ".join(
            f"{fragment}:{count}" for fragment, count in self.fragments.most_common(3)
        )
        accent_profile = ",".join(str(value) for value in self.accents)
        return (
            f"Voices[{ordered_voices}] | Fragments[{ordered_fragments or 'none'}] | Accents[{accent_profile}]"
        )


@dataclass
class LoopResult:
    """Bundle the generated lines with diagnostics and rhythm metadata."""

    lines: List[str]
    diagnostics: LoopDiagnostics
    rhythm: LoopRhythm

    def render(self) -> List[str]:
        diagnostic_line = f"[diagnostics] {self.diagnostics.render_report()}"
        rhythm_line = (
            "Rhythm Pattern: "
            + ",".join(str(value) for value in self.rhythm.accents)
            + f" :: dynamic={','.join(self.rhythm.dynamic_tempi)}"
        )
        return self.lines + [diagnostic_line, rhythm_line]


def _choose_voice(random_state: random.Random, *, previous: str | None = None) -> str:
    """Pick a narrative voice for a line in the loop."""

    voices = [
        "observer",
        "cartographer",
        "chorus",
        "wanderer",
        "signal",
        "dream",
    ]
    pool = [voice for voice in voices if voice != previous] or voices
    return random_state.choice(pool)


def _build_rhythm(seed: LoopSeed, random_state: random.Random) -> LoopRhythm:
    """Construct a rhythmic pattern for the generated loop."""

    base_patterns: Dict[str, List[int]] = {
        "andante": [1, 0, 1, 0],
        "allegro": [1, 1, 0, 1],
        "largo": [1, 0, 0, 0],
        "adagio": [1, 0, 1, 1],
    }
    accents = base_patterns.get(seed.tempo, [1, 0, 1])
    # Rotate the pattern based on a random offset to avoid repeated openings.
    offset = random_state.randrange(len(accents)) if accents else 0
    accents = accents[offset:] + accents[:offset]

    tempi_variants = {
        "andante": ["steady", "gentle", "steady"],
        "allegro": ["quick", "bright", "quick"],
        "largo": ["expansive", "wide", "slow"],
        "adagio": ["calm", "reflective", "lingering"],
    }
    dynamic_tempi = tempi_variants.get(seed.tempo, [seed.tempo, "open", seed.tempo])
    return LoopRhythm(tempo=seed.tempo, pulses=seed.pulses, accents=accents, dynamic_tempi=dynamic_tempi)


def _render_line(
    seed: LoopSeed,
    random_state: random.Random,
    rhythm: LoopRhythm,
    index: int,
    *,
    previous_voice: str | None,
) -> Tuple[str, str, str | None]:
    """Build a single statement within the loop."""

    fragment = random_state.choice(seed.fragments) if seed.fragments else None
    voice = _choose_voice(random_state, previous=previous_voice)

    gestures = {
        "observer": ["notes", "catalogues", "celebrates"],
        "cartographer": ["maps", "sketches", "traces"],
        "chorus": ["sings", "echoes", "harmonizes"],
        "wanderer": ["follows", "collects", "listens for"],
        "signal": ["transmits", "glows for", "amplifies"],
        "dream": ["imagines", "paints", "unfolds"],
    }

    gesture = random_state.choice(gestures[voice])
    subject = fragment or seed.motif
    accent = rhythm.accent_for(index)
    adverb_choices = {
        0: ["gently", "softly", "patiently"],
        1: ["brightly", "boldly", "intently"],
    }
    tempo_hint = random_state.choice(adverb_choices.get(accent, ["brightly"]))
    texture = rhythm.tempo_for(index)

    line = "".join(
        [
            f"The {voice} {gesture} the {subject} {tempo_hint},",
            f" keeping the {texture} cadence {('steady' if accent else 'open')}.",
        ]
    )
    return line, voice, fragment


def generate_loop(seed: LoopSeed) -> LoopResult:
    """Generate the lines for a creative loop."""

    random_state = random.Random(seed.seed)
    rhythm = _build_rhythm(seed, random_state)
    diagnostics = LoopDiagnostics()

    lines: List[str] = []
    previous_voice: str | None = None
    for index in range(seed.pulses):
        line, voice, fragment = _render_line(
            seed,
            random_state,
            rhythm,
            index,
            previous_voice=previous_voice,
        )
        diagnostics.register(voice, fragment, rhythm.accent_for(index))
        lines.append(line)
        previous_voice = voice

    return LoopResult(lines=lines, diagnostics=diagnostics, rhythm=rhythm)


def compose_loop(seed: LoopSeed) -> str:
    """Create a formatted creative loop string."""

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    header = f"Loop for '{seed.motif}' at {timestamp} ({seed.tempo})"
    loop_result = generate_loop(seed)
    body = "\n".join(loop_result.render())
    return "\n".join([header, "", body])


def demo(motif: str, *fragments: str, tempo: str = "andante", pulses: int = 3, seed: int | None = None) -> str:
    """Convenience wrapper for quickly generating a loop."""

    loop_seed = LoopSeed(
        motif=motif,
        fragments=fragments,
        tempo=tempo,
        pulses=pulses,
        seed=seed,
    )
    return compose_loop(loop_seed)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compose a short creative loop.")
    parser.add_argument("motif", help="Primary motif for the loop")
    parser.add_argument(
        "-f",
        "--fragment",
        dest="fragments",
        action="append",
        default=[],
        help="Optional fragment to weave into the loop",
    )
    parser.add_argument(
        "-t",
        "--tempo",
        default="andante",
        help="Tempo hint to include in the header",
    )
    parser.add_argument(
        "-p",
        "--pulses",
        type=int,
        default=3,
        help="Number of statements to generate",
    )
    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        default=None,
        help="Optional seed for deterministic output",
    )

    args = parser.parse_args()
    seed = LoopSeed(
        motif=args.motif,
        fragments=args.fragments,
        tempo=args.tempo,
        pulses=args.pulses,
        seed=args.seed,
    )
    print(compose_loop(seed))
