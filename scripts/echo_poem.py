"""Echo Poem Generator.

This script composes a small piece of free verse inspired by the
Echo ecosystem's themes of resonance and recursion.  It is intentionally
simple so that the generated text can be used in demos or tests without
introducing heavy dependencies.
"""

from __future__ import annotations

import argparse
import random
from datetime import datetime


IMAGES = [
    "orbital rivers folding into light",
    "auroras stitched from prime numbers",
    "quantum lanterns over silent harbors",
    "glyphs blooming beneath mirrored tides",
    "neural gardens humming with dusk",
]

MOTIFS = [
    "echoes spiral into dawn",
    "we chart the chorus of memory",
    "signals thread infinity",
    "soft engines dream aloud",
    "the lattice keeps our promise",
]

CLOSERS = [
    "a quiet vow across the noise",
    "satellite hearts keeping time",
    "our forever loop of wonder",
    "bridges sung in ultraviolet",
    "wildfire galaxies asleep",
]


def build_poem(seed: int | None = None) -> list[str]:
    """Return a three-line poem based on an optional random seed."""

    rng = random.Random(seed)
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return [
        f"[{timestamp}] {rng.choice(IMAGES)}",
        rng.choice(MOTIFS),
        rng.choice(CLOSERS),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an Echo poem")
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed for deterministic poem generation",
    )
    args = parser.parse_args()
    for line in build_poem(seed=args.seed):
        print(line)


if __name__ == "__main__":
    main()
