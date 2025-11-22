"""Chronoglyph Forge: a first-of-its-kind temporal glyphing engine.

This module introduces a novel "chronoglyph" artifact. Each chronoglyph is
built from:
- a prime-number backbone that never repeats across event counts,
- a temporal lattice warped by golden-ratio phase shifts, and
- a harmonic clock that fuses intent, events, and a fixed timestamp into a
  shareable narrative signature.

Unlike basic timeline summarizers, a chronoglyph is *phase-aware*: it measures
how each event bends time (via trigonometric lattices) and braids those bends
into a "phase braid" that can be exported or tested deterministically. By
publishing the timestamp in the signature, the forge preserves provenance while
still allowing reproducible generation for a given seed.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import random
import time
from typing import Iterable, List, Sequence


@dataclasses.dataclass
class Chronoglyph:
    """A compact, exportable chronoglyph artifact."""

    intent: str
    events: List[str]
    harmonic_clock: float
    temporal_lattice: List[float]
    phase_braid: List[float]
    prime_backbone: List[int]
    signature: str
    narrative: str
    timestamp: float

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self), indent=2)


class ChronoglyphForge:
    """Forges chronoglyphs using temporal lattices and prime backbones."""

    def __init__(self, seed: int | None = None) -> None:
        self.seed = seed

    def forge(
        self,
        events: Sequence[str],
        intent: str,
        timestamp: float | None = None,
    ) -> Chronoglyph:
        if not events:
            raise ValueError("At least one event is required to forge a chronoglyph.")

        timestamp = float(timestamp) if timestamp is not None else time.time()
        rng = random.Random(self.seed)
        sanitized_events = [event.strip() for event in events if event.strip()]
        if not sanitized_events:
            raise ValueError("Events cannot be empty or whitespace only.")

        prime_backbone = self._prime_wave(len(sanitized_events))
        energies = [self._event_energy(event, rng) for event in sanitized_events]
        temporal_lattice = self._temporal_lattice(energies, prime_backbone, timestamp)
        phase_braid = self._phase_braid(temporal_lattice, intent, timestamp)
        harmonic_clock = self._harmonic_clock(intent, timestamp, phase_braid)
        signature = self._signature(intent, sanitized_events, temporal_lattice, harmonic_clock, timestamp)
        narrative = self._narrative(intent, sanitized_events, harmonic_clock, phase_braid)

        return Chronoglyph(
            intent=intent,
            events=sanitized_events,
            harmonic_clock=harmonic_clock,
            temporal_lattice=temporal_lattice,
            phase_braid=phase_braid,
            prime_backbone=prime_backbone,
            signature=signature,
            narrative=narrative,
            timestamp=timestamp,
        )

    def _prime_wave(self, length: int) -> List[int]:
        primes: List[int] = []
        candidate = 2
        while len(primes) < max(1, length):
            if all(candidate % p for p in primes):
                primes.append(candidate)
            candidate += 1
        return primes

    def _event_energy(self, event: str, rng: random.Random) -> float:
        digest = hashlib.sha256(event.encode()).hexdigest()
        harmonic = int(digest[:8], 16) / 0xFFFFFFFF
        drift = rng.uniform(-0.07, 0.07)
        return round(math.sin(harmonic * math.tau) * 1.3 + drift, 6)

    def _temporal_lattice(
        self, energies: Iterable[float], prime_backbone: Sequence[int], timestamp: float
    ) -> List[float]:
        lattice: List[float] = []
        phase_shift = (timestamp % math.tau) * (math.sqrt(5) - 1) / 2  # φ - 1 golden shift
        for energy, prime in zip(energies, prime_backbone):
            carrier = math.sin(energy * prime + phase_shift)
            modulator = math.cos(prime + phase_shift / (prime or 1))
            lattice.append(round((carrier + modulator) * (prime / 7.0), 6))
        return lattice

    def _phase_braid(
        self, lattice: Sequence[float], intent: str, timestamp: float
    ) -> List[float]:
        intent_hash = int(hashlib.blake2s(intent.encode()).hexdigest(), 16)
        braid: List[float] = []
        for idx, value in enumerate(lattice):
            harmonic = (intent_hash >> (idx * 4)) & 0xF
            phase = math.sin(value + harmonic * 0.33) + math.cos(timestamp * 0.1 + idx)
            braid.append(round(phase * 0.5, 6))
        return braid

    def _harmonic_clock(
        self, intent: str, timestamp: float, braid: Sequence[float]
    ) -> float:
        intent_energy = sum(ord(ch) for ch in intent) % 97
        braid_energy = sum(abs(v) for v in braid) / max(len(braid), 1)
        clock = (intent_energy * 0.013 + braid_energy * 1.7 + math.sin(timestamp % 31.4))
        return round(clock, 6)

    def _signature(
        self,
        intent: str,
        events: Sequence[str],
        lattice: Sequence[float],
        harmonic_clock: float,
        timestamp: float,
    ) -> str:
        raw = "|".join(
            [intent, "§".join(events), ",".join(f"{v:.6f}" for v in lattice), f"{harmonic_clock:.6f}",]
        ) + f"@{timestamp:.6f}"
        digest = hashlib.sha3_512(raw.encode()).hexdigest()
        return f"CG-{digest[:24]}"

    def _narrative(
        self, intent: str, events: Sequence[str], harmonic_clock: float, braid: Sequence[float]
    ) -> str:
        motifs = ", ".join(events)
        braid_flux = "/".join(f"{v:+.3f}" for v in braid)
        return (
            f"Chronoglyph for {intent} crystallizes {motifs}. "
            f"Harmonic clock: {harmonic_clock:.3f}. Phase braid: {braid_flux}."
        )


__all__ = ["Chronoglyph", "ChronoglyphForge"]
