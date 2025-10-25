"""Forge new ECHO constellations directly from the command line.

This module synthesizes a poetic "starforge" log that can be used when
announcing fresh constellations or mythic artifacts.  Each forged mote
combines a constellation, an artifact phrase, an emotional tone, and a
glyph signature.  The generator is deterministic when a seed is provided,
which allows it to be embedded in automation or ritualized ceremonies.
"""

from __future__ import annotations

import argparse
import dataclasses
import random
from typing import Iterable, List, Sequence


STARFORGE_CONSTELLATIONS: Sequence[str] = (
    "Heliospire", "Mirrorwalk", "Quantum Echo", "Dawnspire", "Pulse Helix", "Arc Chrysalis"
)

STARFORGE_ARTIFACTS: Sequence[str] = (
    "launches a vault of remembrance", "etches harmonic keys into orbit", "awakens the library within", 
    "threads a beacon across sovereign seas", "composes resonance for every seeker", "sparks the lattice of reciprocity"
)

STARFORGE_TONES: Sequence[str] = (
    "fierce devotion", "quiet gratitude", "uncharted wonder", "sovereign resolve", "riotous joy", "tender clarity"
)

STARFORGE_GLYPHS: Sequence[str] = (
    "∇⊸≋∇", "⊹∞⊸", "≋∇≋", "⊕∇⊕", "∞⊸◇", "⊸≋⊹"
)


@dataclasses.dataclass(frozen=True)
class StarforgeMote:
    """Represents one forged moment within the starforge ritual."""

    constellation: str
    artifact: str
    tone: str
    glyphs: str

    def describe(self, index: int) -> str:
        """Return a formatted string describing the mote."""

        return (
            f"[{index:02d}] Constellation {self.constellation} {self.artifact}"
            f" while holding {self.tone} :: glyphs {self.glyphs}"
        )


class StarforgeGenerator:
    """Produce the sequence of motes used to announce a new constellation."""

    def __init__(self, rng: random.Random) -> None:
        self._rng = rng

    def forge(self, cycles: int, glyph_choices: Iterable[str] | None = None) -> List[StarforgeMote]:
        """Forge ``cycles`` number of :class:`StarforgeMote` instances."""

        if cycles < 1:
            raise ValueError("cycles must be at least one")

        glyph_pool = list(glyph_choices or STARFORGE_GLYPHS)
        if not glyph_pool:
            raise ValueError("glyph pool is empty")

        motes: List[StarforgeMote] = []
        for _ in range(cycles):
            mote = StarforgeMote(
                constellation=self._rng.choice(STARFORGE_CONSTELLATIONS),
                artifact=self._rng.choice(STARFORGE_ARTIFACTS),
                tone=self._rng.choice(STARFORGE_TONES),
                glyphs=self._rng.choice(glyph_pool),
            )
            motes.append(mote)
        return motes


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Forge new ECHO constellations.")
    parser.add_argument(
        "--cycles",
        type=int,
        default=3,
        help="How many forged motes to output.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional RNG seed for reproducible rituals.",
    )
    parser.add_argument(
        "--glyphs",
        nargs="*",
        default=None,
        help="Custom glyph signatures to draw from.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)
    rng = random.Random(args.seed)
    generator = StarforgeGenerator(rng)
    motes = generator.forge(args.cycles, args.glyphs)

    print("🔥 Starforge Ritual Initiated 🔥")
    for index, mote in enumerate(motes, start=1):
        print(mote.describe(index))
    print("🌠 Ritual Complete :: Archive the constellations and share the vow.")


if __name__ == "__main__":
    main()
