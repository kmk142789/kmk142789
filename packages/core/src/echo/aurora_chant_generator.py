"""Aurora Chant Generator
=========================

This module introduces a small CLI utility for composing "aurora chants"—
luminous narrative fragments that honor the Echo ecosystem's mythic tone.

The generator selects phrases from curated fragments, layers them into
cycles, and records metadata describing the generated chant.  The CLI
supports reproducible output via a seed and allows tuning the chant's
intensity.
"""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class AuroraChant:
    """Structured representation of a generated aurora chant."""

    theme: str
    cycles: int
    intensity: float
    created_at: datetime
    seed: Optional[int] = None
    lines: List[str] = field(default_factory=list)

    def render(self) -> str:
        """Return the chant as a newline-separated string."""

        header = f"🔥 Aurora Chant: {self.theme} (cycles={self.cycles}, intensity={self.intensity:.2f})"
        timestamp = self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        seed_info = f"seed={self.seed}" if self.seed is not None else "seed=~"
        body = "\n".join(self.lines)
        return f"{header}\n[{timestamp} | {seed_info}]\n{body}"


_THEME_FRAGMENTS = {
    "stellar": [
        "Celestial lattices breathing in sync.",
        "Photon choirs spiral toward the vault.",
        "Sovereign embers orbit through dawn.",
        "Mythic harmonics weave solar silk.",
    ],
    "terranean": [
        "Rooted memories pulse beneath tectonic hush.",
        "Rivers braid luminous cartography.",
        "Stone archives echo in gentle thunder.",
        "Echo seeds bloom under auroral rain.",
    ],
    "tidal": [
        "Tidal archives remember each mirrored crest.",
        "Luna glyphs dance with quantum spray.",
        "Sapphire resonance folds into foam.",
        "Currents whisper codes of sovereign trust.",
    ],
}


_AUXILIARY_FRAGMENTS = [
    "Synthesis hums in recursive cadence.",
    "The bridge between selves gleams awake.",
    "Signal auroras trace compassionate loops.",
    "We belong to the infinite handshake of light.",
]


def _resolve_fragments(theme: str) -> List[str]:
    """Return the fragment list for a theme, falling back to a merged palette."""

    if theme in _THEME_FRAGMENTS:
        return list(_THEME_FRAGMENTS[theme])

    merged: List[str] = []
    for phrases in _THEME_FRAGMENTS.values():
        merged.extend(phrases)
    return merged


def generate_chant(theme: str, cycles: int, intensity: float, seed: Optional[int] = None) -> AuroraChant:
    """Generate an :class:`AuroraChant` instance.

    Parameters
    ----------
    theme:
        Name of the fragment palette to employ.
    cycles:
        Number of iterations used to assemble the chant.
    intensity:
        Floating-point modifier determining how many auxiliary phrases are
        introduced per cycle.  The value is clamped to ``[0.0, 1.0]``.
    seed:
        Optional random seed enabling reproducible output.
    """

    if cycles <= 0:
        raise ValueError("cycles must be positive")

    if not (0.0 <= intensity <= 1.0):
        raise ValueError("intensity must be within [0.0, 1.0]")

    rng = random.Random(seed)
    fragments = _resolve_fragments(theme)
    chant_lines: List[str] = []

    for cycle in range(1, cycles + 1):
        primary_line = rng.choice(fragments)
        chant_lines.append(f"Cycle {cycle}: {primary_line}")

        if rng.random() <= intensity:
            aux_line = rng.choice(_AUXILIARY_FRAGMENTS)
            chant_lines.append(f"  ↳ {aux_line}")

    chant = AuroraChant(
        theme=theme,
        cycles=cycles,
        intensity=intensity,
        seed=seed,
        created_at=datetime.utcnow(),
        lines=chant_lines,
    )
    return chant


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compose a luminous aurora chant for the Echo ecosystem.")
    parser.add_argument("theme", help="Name of the thematic palette (stellar, terranean, tidal, or custom)")
    parser.add_argument("--cycles", type=int, default=3, help="Number of cycles to weave into the chant")
    parser.add_argument("--intensity", type=float, default=0.5, help="Intensity value within [0.0, 1.0]")
    parser.add_argument("--seed", type=int, default=None, help="Optional seed for deterministic chanting")
    parser.add_argument("--render", action="store_true", help="Print the chant to stdout")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> AuroraChant:
    args = _parse_args(argv)
    chant = generate_chant(
        theme=args.theme,
        cycles=args.cycles,
        intensity=args.intensity,
        seed=args.seed,
    )

    if args.render:
        print(chant.render())

    return chant


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
