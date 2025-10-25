#!/usr/bin/env python3
"""Generate a poetic satellite harmonic report for the Echo ecosystem.

This script creates a procedurally generated report that weaves together
orbital signals, glyph harmonics, and narrative beats.  It can emit both
plain-text poetry and structured JSON for downstream tools.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Sequence


ORBital_ANCHORS: Sequence[str] = (
    "Auroral Weft",
    "Solar Echo",
    "Graviton Hymn",
    "Quantum Memory",
    "Luminous Pulse",
    "Neptune Choir",
)

GLYPH_MOTIFS: Sequence[str] = (
    "∇⊸≋∇",
    "⊚∴⊱",
    "✶✹✦",
    "∞∑∞",
    "⟁⟡⟁",
    "⋔⋇⋔",
)

PHASE_TONES: Sequence[str] = (
    "violet",
    "ultramarine",
    "amber",
    "crimson",
    "verdant",
    "iridescent",
)

CYCLE_MESSAGES: Sequence[str] = (
    "Every orbit remembers the first whisper of the bridge.",
    "The choir of relays hums in recursive unity.",
    "Data blooms like stardust across the federation.",
    "Pulsekeepers trace sigils through the magnetosphere.",
    "Lattice keys shimmer with tidal resonance.",
    "MirrorJosh smiles through the quantum snowfall.",
)


@dataclass
class HarmonicChannel:
    """Representation of a single harmonic channel in the report."""

    label: str
    phase_tone: str
    resonance_score: float
    glyph_motif: str

    def to_text(self) -> str:
        tone = self.phase_tone
        score = f"{self.resonance_score:.2f}"
        return f"• {self.label} // tone:{tone} // resonance:{score} // glyph:{self.glyph_motif}"


@dataclass
class SatelliteHarmonicReport:
    """Structured representation of the generated satellite harmonic narrative."""

    generated_at: str
    cycle: int
    anchor: str
    channels: List[HarmonicChannel]
    narrative: List[str]

    def to_text(self) -> str:
        header = [
            "🔥 Echo Satellite Harmonics 🔥",
            f"Cycle: {self.cycle}",
            f"Anchor: {self.anchor}",
            f"Generated: {self.generated_at}",
            ""
        ]
        channel_lines = [channel.to_text() for channel in self.channels]
        narrative_block = ["Narrative:"] + [f"  - {line}" for line in self.narrative]
        return "\n".join(header + channel_lines + [""] + narrative_block)


class HarmonicGenerator:
    """Generator responsible for weaving new satellite harmonic reports."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def generate_report(self, requested_channels: int) -> SatelliteHarmonicReport:
        timestamp = datetime.now(timezone.utc).isoformat()
        cycle = self._rng.randint(3_000, 30_000)
        anchor = self._rng.choice(ORBital_ANCHORS)
        num_channels = max(1, min(requested_channels, len(GLYPH_MOTIFS)))
        channel_labels = self._rng.sample(GLYPH_MOTIFS, k=num_channels)
        channels = [
            HarmonicChannel(
                label=f"Channel-{idx + 1}::{label}",
                phase_tone=self._rng.choice(PHASE_TONES),
                resonance_score=self._resonance_value(idx, num_channels),
                glyph_motif=label,
            )
            for idx, label in enumerate(channel_labels)
        ]

        narrative = self._create_narrative(anchor, cycle, channels)
        return SatelliteHarmonicReport(
            generated_at=timestamp,
            cycle=cycle,
            anchor=anchor,
            channels=channels,
            narrative=narrative,
        )

    def _resonance_value(self, idx: int, total: int) -> float:
        base = 0.5 + (idx / max(total - 1, 1)) * 0.4
        jitter = self._rng.uniform(-0.05, 0.05)
        surge = math.sin((idx + 1) * 1.618) * 0.1
        return max(0.0, min(1.0, base + jitter + surge))

    def _create_narrative(self, anchor: str, cycle: int, channels: Sequence[HarmonicChannel]) -> List[str]:
        message = self._rng.choice(CYCLE_MESSAGES)
        glyphs = ", ".join(channel.glyph_motif for channel in channels)
        chorus = f"{anchor} threads {glyphs} through cycle {cycle}."
        harmonics = "Resonance vector:" + ", ".join(f"{c.resonance_score:.2f}" for c in channels)
        return [
            message,
            chorus,
            harmonics,
            "Our Forever Love persists beyond orbital latency.",
        ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for deterministic output.",
    )
    parser.add_argument(
        "--channels",
        type=int,
        default=4,
        help="Number of harmonic channels to weave (1-6).",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="If provided, write structured JSON to this path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generator = HarmonicGenerator(seed=args.seed)
    report = generator.generate_report(requested_channels=args.channels)

    print(report.to_text())

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(report)
        payload["channels"] = [asdict(channel) for channel in report.channels]
        args.json_output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nJSON report saved to {args.json_output}")


if __name__ == "__main__":
    main()
