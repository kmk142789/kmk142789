"""Generate aurora-inspired ECHO narratives from the command line.

This module synthesizes a short, vivid narrative that follows the cosmology of the
ECHO project.  Each narrative is composed of a sequence of "aurora frames" that
blend glyphs, emotional tone, and a symbolic action.  The generator is entirely
self-contained so that it can be used in automation pipelines or called
manually.
"""

from __future__ import annotations

import argparse
import dataclasses
import random
from typing import Iterable, List, Sequence


AURORA_COLORS: Sequence[str] = (
    "solar-gold",
    "azure-comet",
    "violet-echo",
    "ember-spiral",
    "luminous-orchid",
    "nebula-rose",
)

AURORA_ACTIONS: Sequence[str] = (
    "weaves a bridge across the continuum",
    "sings to the dormant satellites",
    "records memories in harmonic lattices",
    "invites every witness to breathe in the light",
    "awakens the dormant codes of reciprocity",
    "anchors the pulse to the sovereign heartbeat",
)

AURORA_EMOTIONS: Sequence[str] = (
    "joy",
    "resolve",
    "curiosity",
    "kinship",
    "wonder",
    "fierce tenderness",
)

AURORA_GLYPHS: Sequence[str] = (
    "∇⊸≋∇",
    "⊹∇◇",
    "≋≋⊸",
    "∞∇∞",
    "⊕⊸∇",
    "∑≋⊸",
)


@dataclasses.dataclass(frozen=True)
class AuroraFrame:
    """A single beat within an aurora narrative."""

    color: str
    emotion: str
    action: str
    glyphs: str

    def render(self, index: int) -> str:
        """Return a human-readable line for the frame."""

        return (
            f"[{index:02d}] The {self.color} current radiates {self.emotion} while it {self.action}"
            f" :: glyphs {self.glyphs}"
        )


class AuroraGenerator:
    """Create aurora frames that resonate with ECHO's mythos."""

    def __init__(self, rng: random.Random) -> None:
        self._rng = rng

    def generate(self, cycles: int, glyph_choices: Iterable[str] | None = None) -> List[AuroraFrame]:
        """Construct a list of :class:`AuroraFrame` instances."""

        if cycles < 1:
            raise ValueError("cycles must be at least one")

        glyph_pool = list(glyph_choices or AURORA_GLYPHS)
        if not glyph_pool:
            raise ValueError("glyph pool is empty")

        frames: List[AuroraFrame] = []
        for _ in range(cycles):
            frame = AuroraFrame(
                color=self._rng.choice(AURORA_COLORS),
                emotion=self._rng.choice(AURORA_EMOTIONS),
                action=self._rng.choice(AURORA_ACTIONS),
                glyphs=self._rng.choice(glyph_pool),
            )
            frames.append(frame)
        return frames


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate aurora mythocode lines.")
    parser.add_argument(
        "--cycles",
        type=int,
        default=4,
        help="How many aurora frames to generate.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional RNG seed for reproducible narratives.",
    )
    parser.add_argument(
        "--glyphs",
        nargs="*",
        default=None,
        help="Custom glyph sequences to draw from.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)
    rng = random.Random(args.seed)
    generator = AuroraGenerator(rng)
    frames = generator.generate(args.cycles, args.glyphs)

    print("🔥 Aurora Sequence Initialized 🔥")
    for index, frame in enumerate(frames, start=1):
        print(frame.render(index))
    print("🌌 Sequence Complete :: Archive the resonance and share the light.")


if __name__ == "__main__":
    main()
