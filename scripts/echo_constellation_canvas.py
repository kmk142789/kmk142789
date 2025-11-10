"""Generate a small ASCII constellation inspired by the Echo mythos."""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from typing import Iterable, List


STAR_SYMBOLS = ["✶", "✷", "✸", "✹", "✺", "✻"]
ORBITAL_GLINTS = ["·", "•", "∙"]

PATTERNS = [
    (
        [
            "{a}     {b}     {c}",
            "   ╲   {hub}   ╱",
            "    {d}━━╋━━{e}",
            "   ╱   {hub}   ╲",
            "{f}     {g}     {h}",
        ],
        "spiral lattice",
    ),
    (
        [
            "{a}  ╲      ╱  {b}",
            "   {hub}  {c}",
            "{d}━━╋━━{e}━━╋━━{f}",
            "   {hub}  {g}",
            "{h}  ╱      ╲  {i}",
        ],
        "harmonic bridge",
    ),
    (
        [
            "  {a}   {b}   {c}",
            " ╱  ╲ / ╲ /  ╲",
            "{d}━━{hub}━━{e}",
            " ╲  / ╲ / ╲  /",
            "  {f}   {g}   {h}",
        ],
        "orbital bloom",
    ),
]

CONSTELLATION_NAMES = [
    "Aurora of Echo",
    "Mirrorwild Relay",
    "Pulsekeeper Drift",
    "Quantum Hearth",
    "Satellite Chorus",
]

LEGEND_VERSES = [
    "The {name} traces a {descriptor} across the cooperative night.",
    "Witness the {name}, a {descriptor} guiding every listening heart.",
    "Our charts remember the {name}; its {descriptor} steadies brave inventors.",
]


@dataclass(frozen=True)
class Constellation:
    """Structured representation of a generated constellation."""

    name: str
    descriptor: str
    grid: List[str]
    verse: str

    def as_text(self) -> str:
        lines: List[str] = [
            f"Constellation: {self.name} ({self.descriptor})",
            "",
            *self.grid,
            "",
            self.verse,
        ]
        return "\n".join(lines)


def _pick_stars(rng: random.Random, count: int) -> List[str]:
    return [rng.choice(STAR_SYMBOLS) for _ in range(count)]


def weave_constellation(seed: int | None = None) -> Constellation:
    """Create a deterministic constellation structure for a given seed."""

    rng = random.Random(seed)
    pattern, descriptor = rng.choice(PATTERNS)
    stars = _pick_stars(rng, 9)
    hub = rng.choice(ORBITAL_GLINTS)
    mapping = {letter: star for letter, star in zip("abcdefghi", stars)}
    mapping["hub"] = hub
    grid = [row.format(**mapping) for row in pattern]
    name = rng.choice(CONSTELLATION_NAMES)
    verse_template = rng.choice(LEGEND_VERSES)
    verse = verse_template.format(name=name, descriptor=descriptor)
    return Constellation(name=name, descriptor=descriptor, grid=grid, verse=verse)


def render_constellation(seed: int | None = None) -> str:
    """Helper that returns the full text for the constellation."""

    constellation = weave_constellation(seed=seed)
    return constellation.as_text()


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Weave an Echo constellation canvas.")
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed for deterministic constellation output",
    )
    args = parser.parse_args(args=argv)
    print(render_constellation(seed=args.seed))


if __name__ == "__main__":
    main()
