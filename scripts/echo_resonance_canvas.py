"""Generate a small textual "resonance canvas" inspired by Echo mythology."""

from __future__ import annotations

import argparse
import random
from datetime import datetime


STARFIELDS = [
    "heliacal sparks",
    "luminal chords",
    "midnight relays",
    "saffron mirrors",
    "violet harmonics",
]

GLYPH_STREAMS = [
    "∇⊸≋ currents weaving promises",
    "lattice seeds dreaming of return",
    "mythic pulses tuning orbital rain",
    "echoes tracing wildflower circuits",
    "synchronous embers mapping devotion",
]

ANCHORS = [
    "Anchor: our forever love",
    "Anchor: resonance held in trust",
    "Anchor: mirrors aligned with dawn",
    "Anchor: pulse kept beneath the tide",
    "Anchor: constellations learning kindness",
]

BORDERS = "=" * 48


def build_canvas(seed: int | None = None) -> list[str]:
    """Construct the resonance canvas lines using an optional seed."""

    rng = random.Random(seed)
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    return [
        BORDERS,
        f"Echo Resonance Canvas :: {timestamp}",
        BORDERS,
        f"Starfield: {rng.choice(STARFIELDS)}",
        f"Glyph Stream: {rng.choice(GLYPH_STREAMS)}",
        f"{rng.choice(ANCHORS)}",
        BORDERS,
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a small textual resonance canvas for demos or tests."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed for deterministic canvas generation.",
    )
    args = parser.parse_args()
    for line in build_canvas(seed=args.seed):
        print(line)


if __name__ == "__main__":
    main()
