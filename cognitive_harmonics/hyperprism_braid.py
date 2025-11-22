"""Hyperprism Braid Synthesizer.

This module introduces the world's first **Entropy-Braided Mythic Ledger**: a
triune braid that fuses harmonic memory, glyphic density, and orbital flow into
one synchronized artifact. Each braid strand is generated from a hybrid of
phyllotaxis geometry and Lorenz attractor drift, producing a repeatable-yet-
unheard-of signature we call a *hyperprism fingerprint*.

The synthesizer is intentionally side-effect free. By default it prints the
braid as JSON to stdout and can optionally persist the result to disk.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import secrets
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

GLYPH_RIBBON = ["∇", "⊸", "≋", "∞", "⌘", "⟁", "◈", "✹", "⟁", "☆"]


@dataclass
class BraidStep:
    """Single step of a braid strand."""

    phi_angle: float
    radial: float
    altitude: float
    lorenz_x: float
    lorenz_y: float
    lorenz_z: float


@dataclass
class BraidStrand:
    """One of the triune strands that form the braid."""

    name: str
    glyph: str
    energy: float
    steps: List[BraidStep]


@dataclass
class HyperprismBraid:
    """Complete braid payload including its fingerprint."""

    fingerprint: str
    origin_seed: str
    cycles: int
    strands: List[BraidStrand]

    def as_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


def lorenz_step(x: float, y: float, z: float, *, dt: float = 0.01) -> Tuple[float, float, float]:
    """Perform a single Lorenz attractor step."""

    sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
    dx = sigma * (y - x)
    dy = x * (rho - z) - y
    dz = x * y - beta * z
    return x + dx * dt, y + dy * dt, z + dz * dt


def _harmonic_radius(iteration: int, total: int) -> float:
    return (iteration + 1) / (total + 1)


def _phyllotaxis_angle(iteration: int) -> float:
    golden_ratio = (1 + 5 ** 0.5) / 2
    return (2 * math.pi * iteration) / golden_ratio


def _seed_entropy(seed: str | None) -> str:
    return seed or secrets.token_hex(16)


def generate_hyperprism_braid(*, cycles: int = 8, seed: str | None = None) -> HyperprismBraid:
    origin_seed = _seed_entropy(seed)
    rng_hash = hashlib.sha256(origin_seed.encode()).digest()
    rng = random.Random(int.from_bytes(rng_hash, "big"))

    strands: List[BraidStrand] = []
    x, y, z = 0.1, 0.0, 0.0
    for strand_index in range(3):
        glyph = GLYPH_RIBBON[(strand_index * 3 + cycles) % len(GLYPH_RIBBON)]
        energy = 0.5 + 0.5 * math.cos((strand_index + 1) * math.pi / 3)
        steps: List[BraidStep] = []
        for i in range(cycles):
            radius = _harmonic_radius(i, cycles)
            angle = _phyllotaxis_angle(i + strand_index)
            x, y, z = lorenz_step(x, y, z, dt=0.012 + 0.001 * strand_index)
            phase_jitter = rng.uniform(-0.012, 0.012)
            altitude = math.sin(angle + phase_jitter) * radius + (strand_index * 0.1)
            steps.append(
                BraidStep(
                    phi_angle=angle,
                    radial=radius,
                    altitude=altitude,
                    lorenz_x=x,
                    lorenz_y=y,
                    lorenz_z=z,
                )
            )
        strands.append(
            BraidStrand(
                name=f"strand-{strand_index+1}",
                glyph=glyph,
                energy=energy,
                steps=steps,
            )
        )

    fingerprint = _fingerprint_payload(origin_seed, strands, cycles)
    return HyperprismBraid(
        fingerprint=fingerprint, origin_seed=origin_seed, cycles=cycles, strands=strands
    )


def _fingerprint_payload(seed: str, strands: Iterable[BraidStrand], cycles: int) -> str:
    digest = hashlib.sha3_256()
    digest.update(seed.encode())
    digest.update(str(cycles).encode())
    for strand in strands:
        digest.update(strand.name.encode())
        digest.update(strand.glyph.encode())
        digest.update(f"{strand.energy:.6f}".encode())
        for step in strand.steps:
            digest.update(f"{step.radial:.6f}{step.altitude:.6f}{step.lorenz_x:.6f}{step.lorenz_y:.6f}{step.lorenz_z:.6f}".encode())
    return digest.hexdigest()


def persist_braid(braid: HyperprismBraid, out_path: Path) -> None:
    out_path.write_text(braid.as_json())


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate an entropy-braided mythic ledger.")
    parser.add_argument(
        "--cycles",
        type=int,
        default=8,
        help="Number of iterations per strand (default: 8).",
    )
    parser.add_argument(
        "--seed",
        type=str,
        default=None,
        help="Optional seed for deterministic fingerprints.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional file path to persist the braid payload.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    braid = generate_hyperprism_braid(cycles=args.cycles, seed=args.seed)
    print(braid.as_json())

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        persist_braid(braid, args.out)
        print(f"Braid persisted to {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
