"""Orbital Memory Fabric: a world-first mythogenic braid synthesizer.

This module spins multi-directional memory strands into a temporal fingerprint. It is
intentionally small yet expressive so that downstream tools can stitch the resulting
"orbital blueprint" into broader Echo workflows.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import blake2b
import json
from typing import Iterable, List, Sequence

GOLDEN_RATIO = 1.618033988749895


@dataclass(frozen=True)
class MemoryStrand:
    """Represents a single strand in the orbital braid."""

    seed: str
    checksum: str
    harmonic: float
    braid_index: int

    def as_dict(self) -> dict[str, str | float | int]:
        return {
            "seed": self.seed,
            "checksum": self.checksum,
            "harmonic": round(self.harmonic, 6),
            "braid_index": self.braid_index,
        }


@dataclass(frozen=True)
class FabricOutcome:
    """Container for the synthesized blueprint."""

    epoch: datetime
    spectral_flux: str
    palindrome: str
    strands: List[MemoryStrand]
    orbit_stamp: str
    fingerprint: str

    def to_json(self) -> str:
        payload = {
            "epoch": self.epoch.isoformat(),
            "spectral_flux": self.spectral_flux,
            "palindrome": self.palindrome,
            "strands": [strand.as_dict() for strand in self.strands],
            "orbit_stamp": self.orbit_stamp,
            "fingerprint": self.fingerprint,
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def render_blueprint(self) -> str:
        strand_lines = "\n".join(
            f"  • {strand.seed} :: {strand.checksum[:10]} :: {strand.harmonic:.3f}"
            for strand in self.strands
        )
        return (
            "ORBITAL MEMORY FABRIC\n"
            f"Epoch: {self.epoch.isoformat()}\n"
            f"Spectral Flux: {self.spectral_flux}\n"
            f"Orbit Stamp: {self.orbit_stamp}\n"
            f"Palindrome Spine: {self.palindrome}\n"
            "Strands:\n"
            f"{strand_lines}\n"
            f"Fingerprint: {self.fingerprint}"
        )


class OrbitalMemoryFabric:
    """Synthesizes a directional memory braid with a temporal orbit signature."""

    def __init__(self, seeds: Sequence[str], cycles: int = 3, epoch: datetime | None = None):
        if not seeds:
            raise ValueError("At least one seed is required to braid the fabric.")
        if cycles < 1:
            raise ValueError("Cycle count must be positive.")

        self.seeds = [seed.strip() for seed in seeds if seed.strip()]
        if not self.seeds:
            raise ValueError("All provided seeds were empty after stripping whitespace.")

        self.cycles = cycles
        self.epoch = epoch or datetime.now(timezone.utc)

    def _hash_seed(self, seed: str, index: int) -> str:
        # We bind the seed to both its position and the epoch to produce a non-replayable braid.
        hasher = blake2b(digest_size=20)
        hasher.update(seed.encode("utf-8"))
        hasher.update(str(index).encode("utf-8"))
        hasher.update(str(self.epoch.timestamp()).encode("utf-8"))
        return hasher.hexdigest()

    def _harmonic(self, seed: str, index: int) -> float:
        # Golden-ratio weighting with a lattice offset to avoid symmetry collapse.
        return (len(seed) + (index + 1) ** 2) / GOLDEN_RATIO

    def _build_palindrome(self, sequence: Iterable[str]) -> str:
        forward = " | ".join(sequence)
        reverse = " | ".join(reversed(list(sequence)))
        return f"{forward} || {reverse}"

    def braid(self) -> FabricOutcome:
        strands: list[MemoryStrand] = []
        for cycle in range(self.cycles):
            seed = self.seeds[cycle % len(self.seeds)]
            checksum = self._hash_seed(seed, cycle)
            strands.append(
                MemoryStrand(
                    seed=seed,
                    checksum=checksum,
                    harmonic=self._harmonic(seed, cycle),
                    braid_index=cycle,
                )
            )

        spectral_flux = self._spectral_flux(strands)
        palindrome = self._build_palindrome(seed for seed in self.seeds)
        orbit_stamp = self._orbit_stamp()
        fingerprint = self._fingerprint(spectral_flux, orbit_stamp)

        return FabricOutcome(
            epoch=self.epoch,
            spectral_flux=spectral_flux,
            palindrome=palindrome,
            strands=strands,
            orbit_stamp=orbit_stamp,
            fingerprint=fingerprint,
        )

    def _spectral_flux(self, strands: Sequence[MemoryStrand]) -> str:
        flux_bits = "".join(str(int(strand.harmonic * 1000) % 7) for strand in strands)
        rotated = flux_bits[-1] + flux_bits[:-1] if flux_bits else "0"
        return f"Φ{flux_bits}|{rotated}"

    def _orbit_stamp(self) -> str:
        epoch_seconds = int(self.epoch.timestamp())
        braided = int(epoch_seconds * GOLDEN_RATIO) ^ len(self.seeds) ^ self.cycles
        return f"ORBIT-{braided:x}"

    def _fingerprint(self, spectral_flux: str, orbit_stamp: str) -> str:
        raw = f"{spectral_flux}::{orbit_stamp}::{len(self.seeds)}::{self.cycles}"
        return blake2b(raw.encode("utf-8"), digest_size=12).hexdigest()


def main() -> int:  # pragma: no cover - thin CLI wrapper
    import argparse

    parser = argparse.ArgumentParser(description="Orbital Memory Fabric synthesizer")
    parser.add_argument(
        "--seed",
        "-s",
        action="append",
        required=True,
        help="Seed strings that anchor the braid (repeatable)",
    )
    parser.add_argument(
        "--cycles",
        "-c",
        type=int,
        default=3,
        help="Number of cycles to weave through the fabric",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the blueprint as JSON instead of formatted text",
    )
    args = parser.parse_args()

    fabric = OrbitalMemoryFabric(seeds=args.seed, cycles=args.cycles)
    outcome = fabric.braid()

    if args.json:
        print(outcome.to_json())
    else:
        print(outcome.render_blueprint())

    return 0


if __name__ == "__main__":  # pragma: no cover - command line entry point
    raise SystemExit(main())
