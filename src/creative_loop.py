"""Creative loop generator for playful improvisations.

This module creates short clusters of statements that orbit around a motif.
Each loop is designed to feel rhythmic, blending observational language with
imaginative declarations.  The module can be imported as a library or used
from the command line to print a loop to stdout.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import random
from typing import Iterable, List


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


def _choose_voice(random_state: random.Random) -> str:
    """Pick a narrative voice for a line in the loop."""

    voices = [
        "observer",
        "cartographer",
        "chorus",
        "wanderer",
        "signal",
        "dream",
    ]
    return random_state.choice(voices)


def _render_line(seed: LoopSeed, random_state: random.Random) -> str:
    """Build a single statement within the loop."""

    fragment = random_state.choice(seed.fragments) if seed.fragments else None
    voice = _choose_voice(random_state)

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
    tempo_hint = random_state.choice(["gently", "brightly", "patiently", "boldly"])

    return f"The {voice} {gesture} the {subject} {tempo_hint}."


def generate_loop(seed: LoopSeed) -> List[str]:
    """Generate the lines for a creative loop."""

    random_state = random.Random(seed.seed)
    lines = [_render_line(seed, random_state) for _ in range(seed.pulses)]
    return lines


def compose_loop(seed: LoopSeed) -> str:
    """Create a formatted creative loop string."""

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    header = f"Loop for '{seed.motif}' at {timestamp} ({seed.tempo})"
    body = "\n".join(generate_loop(seed))
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
