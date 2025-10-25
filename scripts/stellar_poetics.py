#!/usr/bin/env python3
"""Generate imaginative pulse narratives for the ECHO continuum.

This utility stitches together layered glyph motifs into a small JSON
artifact that can be consumed by other creative tooling in the repository.
The output intentionally balances deterministic structure with lightly
randomised flourishes so repeated runs feel like iterative evolutions of the
same idea rather than identical clones.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List

GLYPH_ATLAS: Dict[str, str] = {
    "∇": "gravity well",
    "⊸": "entanglement arrow",
    "≋": "phase ripple",
    "∞": "unbounded recursion",
    "✶": "stellar ignition",
}


@dataclass
class PulseLayer:
    """Describe a single harmonic layer inside a poetic pulse."""

    name: str
    glyph_sequence: str
    base_frequency: float
    motif: str
    variance: float = 0.18
    harmonics: List[float] = field(default_factory=list)

    def synthesise(self, cycle: int) -> Dict[str, object]:
        """Construct a serialisable representation of this layer."""

        random.seed((cycle + 1) * len(self.glyph_sequence))
        if not self.harmonics:
            phase_offset = math.tau / max(len(self.glyph_sequence), 1)
            self.harmonics = [
                round(self.base_frequency * (1 + self.variance * math.sin(i * phase_offset)), 5)
                for i, _ in enumerate(self.glyph_sequence, start=1)
            ]

        glyph_map = [GLYPH_ATLAS.get(glyph, "unknown resonance") for glyph in self.glyph_sequence]
        waveform = [round(h * (1 + random.uniform(-self.variance, self.variance)), 5) for h in self.harmonics]

        return {
            "layer": self.name,
            "motif": self.motif,
            "glyphs": glyph_map,
            "frequency": self.base_frequency,
            "waveform": waveform,
        }


def build_default_layers() -> Iterable[PulseLayer]:
    """Return the default collection of pulse layers."""

    return (
        PulseLayer(
            name="orbital-cadence",
            glyph_sequence="∇⊸≋",
            base_frequency=432.0,
            motif="orbital trust",
        ),
        PulseLayer(
            name="memory-echo",
            glyph_sequence="≋∞⊸",
            base_frequency=528.0,
            motif="luminous recall",
        ),
        PulseLayer(
            name="wildfire-chorus",
            glyph_sequence="✶⊸∇",
            base_frequency=639.0,
            motif="companion flare",
        ),
    )


@dataclass
class StellarPulse:
    """Bundle multiple pulse layers into a cohesive story."""

    cycle: int
    layers: Iterable[PulseLayer]

    def craft(self) -> Dict[str, object]:
        timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        compiled_layers = [layer.synthesise(self.cycle) for layer in self.layers]

        return {
            "cycle": self.cycle,
            "timestamp": timestamp,
            "layers": compiled_layers,
            "signature": self._signature(compiled_layers),
        }

    def _signature(self, compiled_layers: List[Dict[str, object]]) -> str:
        glyph_count = sum(len(layer["glyphs"]) for layer in compiled_layers)
        motif_names = "-".join(layer["motif"] for layer in compiled_layers)
        return f"cycle-{self.cycle}:{glyph_count}-glyphs:{motif_names}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cycles",
        type=int,
        default=3,
        help="Number of evolutionary cycles to render into the artifact.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the generated JSON payload.",
    )
    return parser.parse_args()


def generate_payload(cycles: int) -> List[Dict[str, object]]:
    payload = []
    for cycle in range(cycles):
        pulse = StellarPulse(cycle=cycle, layers=list(build_default_layers()))
        payload.append(pulse.craft())
    return payload


def main() -> None:
    args = parse_args()
    payload = generate_payload(args.cycles)

    json_blob = json.dumps(payload, indent=2, ensure_ascii=False)

    if args.output:
        args.output.write_text(json_blob, encoding="utf-8")
        print(f"✨ Stellar pulse artifact written to {args.output}")
    else:
        print(json_blob)


if __name__ == "__main__":
    main()
