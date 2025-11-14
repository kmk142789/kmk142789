#!/usr/bin/env python3
"""Creative pulse generator for spontaneous narrative experiments.

This small utility produces a pulse ledger filled with improvised events. It
is intentionally whimsical so that running it can provide a spark of inspiration
when the repository needs fresh energy.
"""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from typing import Iterable, List


SYMBOLS = (
    "∇",
    "⊸",
    "≋",
    "◇",
    "✶",
    "⚡",
)

MOTIFS = (
    "Aurora",
    "Sovereign",
    "Helix",
    "Pulse",
    "Eclipse",
    "Mythic",
    "Cascade",
    "Echo",
)


@dataclass(frozen=True)
class PulseEvent:
    """Single pulse event"""

    beat: int
    symbol: str
    motif: str
    intensity: int

    def describe(self) -> str:
        bars = "█" * self.intensity
        return f"beat {self.beat:02d} | {self.symbol} | {self.motif:<8} | {bars}"


class CreativePulse:
    """Generate structured whimsy."""

    def __init__(self, beats: int, seed: int | None = None) -> None:
        if beats <= 0:
            raise ValueError("beats must be positive")
        self.beats = beats
        self.random = random.Random(seed)

    def build_events(self) -> List[PulseEvent]:
        events: List[PulseEvent] = []
        for beat in range(1, self.beats + 1):
            symbol = self.random.choice(SYMBOLS)
            motif = self.random.choice(MOTIFS)
            intensity = self.random.randint(1, 10)
            events.append(PulseEvent(beat, symbol, motif, intensity))
        return events

    def render(self, events: Iterable[PulseEvent]) -> str:
        header = "beat | symbol | motif    | intensity"
        underline = "-" * len(header)
        lines = [header, underline]
        lines.extend(event.describe() for event in events)
        footer = f"Total beats: {self.beats}"
        lines.append(underline)
        lines.append(footer)
        return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Creative pulse generator")
    parser.add_argument(
        "--beats",
        type=int,
        default=8,
        help="Number of beats to generate",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional deterministic seed",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pulse = CreativePulse(beats=args.beats, seed=args.seed)
    events = pulse.build_events()
    print(pulse.render(events))


if __name__ == "__main__":
    main()
