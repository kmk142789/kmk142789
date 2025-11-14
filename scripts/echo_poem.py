"""Utility for generating small Echo-themed poems.

This module provides a tiny creative playground that can be used from the
command line or imported in other tooling.  It mixes together a handful of
motifs in deterministic ways if the caller provides a seed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List
import argparse
import random


@dataclass(frozen=True)
class EchoMotif:
    """Simple container for a motif's vocabulary.

    Attributes:
        name: Friendly label shown in debugging output.
        imagery: Words or phrases evoking the motif's visual component.
        cadence: Short fragments hinting at rhythm or intent.
    """

    name: str
    imagery: Iterable[str]
    cadence: Iterable[str]

    def craft_line(self, rng: random.Random) -> str:
        """Return a single line inspired by the motif."""

        subject = rng.choice(tuple(self.imagery))
        rhythm = rng.choice(tuple(self.cadence))
        return f"{rhythm} {subject}".strip()


DEFAULT_MOTIFS: List[EchoMotif] = [
    EchoMotif(
        name="Signal",
        imagery=("auroral filament", "resonant lattice", "midnight semaphore"),
        cadence=("We echo", "We remember", "We breathe for"),
    ),
    EchoMotif(
        name="Wildfire",
        imagery=("ember chorus", "flaring archive", "solar hush"),
        cadence=("The wildfire hums", "Kindled by", "Orbiting"),
    ),
    EchoMotif(
        name="Harbor",
        imagery=("tidal ledger", "harboring archive", "gentle delta"),
        cadence=("Come rest beside", "Folded into", "Trace a path across"),
    ),
]


def generate_poem(theme: str, lines: int = 4, seed: int | None = None) -> str:
    """Generate a short poem celebrating the provided theme.

    Args:
        theme: Highlighted word or phrase threaded through the poem.
        lines: The number of lines to produce (minimum of one).
        seed: Optional random seed for deterministic output.
    """

    if lines < 1:
        raise ValueError("lines must be at least 1")

    rng = random.Random(seed)
    selected_motifs = rng.sample(DEFAULT_MOTIFS, k=len(DEFAULT_MOTIFS))

    poem_lines = []
    for i in range(lines):
        motif = selected_motifs[i % len(selected_motifs)]
        crafted = motif.craft_line(rng)
        poem_lines.append(f"{crafted} — {theme}")

    return "\n".join(poem_lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "theme",
        nargs="?",
        default="Echo continuum",
        help="Word or phrase to anchor the poem (default: 'Echo continuum')",
    )
    parser.add_argument(
        "-n",
        "--lines",
        type=int,
        default=4,
        help="Number of lines to generate (default: 4)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for deterministic output",
    )
    return parser


def main(argv: list[str] | None = None) -> str:
    parser = build_parser()
    args = parser.parse_args(argv)
    poem = generate_poem(args.theme, lines=args.lines, seed=args.seed)
    print(poem)
    return poem


if __name__ == "__main__":
    main()
