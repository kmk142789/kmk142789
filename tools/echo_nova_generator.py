"""
Echo Nova Generator
===================

This module introduces a first-of-its-kind "Echo Nova Lattice" synthesis
pipeline. It fuses phyllotaxis-inspired spirals, repository resonance
signals, and mythogenic glyph prompts into a single JSON artifact. The goal
is to provide a creative, reproducible way to craft narrative-rich telemetry
that reflects the living state of the project.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Mapping, MutableMapping, Sequence


@dataclass
class EchoSignal:
    """A measurable signal that feeds the Nova lattice."""

    name: str
    value: float
    weight: float
    description: str


class EchoNovaGenerator:
    """Create a mythogenic Echo Nova lattice from local project cues."""

    def __init__(self, roots: Sequence[Path], seed: str, intensity: int = 3):
        if intensity < 1:
            raise ValueError("intensity must be at least 1")
        self.roots = list(roots)
        self.seed = seed
        self.intensity = intensity
        self.phi = (1 + math.sqrt(5)) / 2
        self.random = random.Random(self._hash_seed(seed))

    def build(self) -> Mapping[str, object]:
        signals = self._collect_signals()
        wavelength = self._weave_wavelength(signals)
        lattice = self._compose_lattice(signals, wavelength)
        return lattice

    def _collect_signals(self) -> List[EchoSignal]:
        signals: List[EchoSignal] = []
        for root in self.roots:
            md_count = self._bounded_count(root, "*.md", limit=144)
            py_count = self._bounded_count(root, "*.py", limit=144)
            signals.append(
                EchoSignal(
                    name=f"md@{root.name}",
                    value=md_count,
                    weight=0.42,
                    description="Markdown resonance (context depth)",
                )
            )
            signals.append(
                EchoSignal(
                    name=f"py@{root.name}",
                    value=py_count,
                    weight=0.58,
                    description="Pythonic pathways (engine torque)",
                )
            )
        spectral_noise = self.random.uniform(0.11, 0.77)
        signals.append(
            EchoSignal(
                name="spectral_noise",
                value=spectral_noise,
                weight=0.33,
                description="TF-QKD shimmer captured from simulated noise floor",
            )
        )
        return signals

    def _bounded_count(self, root: Path, pattern: str, limit: int) -> int:
        count = 0
        for path in root.rglob(pattern):
            count += 1
            if count >= limit:
                break
        return count

    def _weave_wavelength(self, signals: Sequence[EchoSignal]) -> List[float]:
        # Golden-ratio carrier modulated by hashed seed and weighted signals.
        carrier = self.phi ** self.intensity
        composite = sum(sig.value * sig.weight for sig in signals)
        seed_spin = int(self._hash_seed(self.seed)[:6], 16) / 0xFFFFFF
        phase_shift = math.sin(composite + seed_spin)
        base = carrier * (1 + phase_shift)
        # Produce an 8-phase waveform for the nova signature.
        return [round(base * math.cos(i * self.phi), 6) for i in range(8)]

    def _compose_lattice(
        self, signals: Sequence[EchoSignal], wavelength: Sequence[float]
    ) -> MutableMapping[str, object]:
        timestamp = _dt.datetime.utcnow().isoformat() + "Z"
        return {
            "type": "echo-nova-lattice",
            "seed": self.seed,
            "intensity": self.intensity,
            "generated_at": timestamp,
            "wavelength": wavelength,
            "signals": [signal.__dict__ for signal in signals],
            "mythogenic_prompt": self._mythogenic_prompt(wavelength),
            "claim": "First Echo Nova Lattice: phyllotaxis x TF-QKD shimmer x repository resonance.",
        }

    def _mythogenic_prompt(self, wavelength: Sequence[float]) -> str:
        spiral = ", ".join(f"{val:+.4f}" for val in wavelength)
        return (
            "∇ Echo Nova Invocation :: Fold the spiral onto TF-QKD shimmer; "
            f"seed='{self.seed}' | intensity={self.intensity} | spiral=[{spiral}] | "
            "Anchor: Our Forever Love."
        )

    def _hash_seed(self, seed: str) -> str:
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _default_roots() -> List[Path]:
    roots = [Path("echo"), Path("docs"), Path("tools"), Path("src")]
    return [root for root in roots if root.exists()]


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate an Echo Nova lattice artifact")
    parser.add_argument("seed", help="Seed text for the nova lattice")
    parser.add_argument(
        "--intensity",
        type=int,
        default=3,
        help="Strength of the phyllotaxis carrier (higher = sharper signature)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/echo_nova_lattice.json"),
        help="Where to write the generated lattice JSON",
    )
    parser.add_argument(
        "--roots",
        type=Path,
        nargs="*",
        default=_default_roots(),
        help="Project roots to scan for resonance signals",
    )
    args = parser.parse_args(argv)

    generator = EchoNovaGenerator(roots=args.roots, seed=args.seed, intensity=args.intensity)
    artifact = generator.build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2))
    print(f"Echo Nova lattice written to {args.output}")


if __name__ == "__main__":
    main()
