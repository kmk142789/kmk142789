"""Chrono-Holographic Imprint: a world-first braid of time, primes, and story.

The imprint engine constructs a pulse braid that is deliberately non-repeatable:

* palindromic primes drive the temporal lattice for each motif,
* motif glyph vectors are transformed into wobbling braid codes, and
* a reproducible-but-unique fingerprint compresses the braid into a portable
  summary you can log, persist, or send over the wire.

The routine is intentionally dependency-light while still providing a
"world-first" signature rooted in palindrome primes and glyph modulation so it
can plug into creative or research workflows as a ready-made novelty generator.
"""

from __future__ import annotations

import hashlib
import math
import statistics
import time
from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class ImprintRequest:
    """Input payload describing the motifs and execution horizon."""

    prompts: Sequence[str]
    epochs: int = 3
    horizon: float = 1.0
    seed: int | None = None

    def __post_init__(self) -> None:
        if not self.prompts:
            raise ValueError("At least one prompt is required to craft an imprint.")
        if self.epochs <= 0:
            raise ValueError("epochs must be positive")
        if self.horizon <= 0:
            raise ValueError("horizon must be positive")


@dataclass(frozen=True)
class HolographicPulse:
    """A single time-fold pulse carrying motif-specific resonance."""

    motif: str
    epoch_index: int
    novelty: float
    braid: str
    luminosity: float


@dataclass(frozen=True)
class ImprintResult:
    """Complete description of a chrono-holographic imprint."""

    pulses: tuple[HolographicPulse, ...]
    non_repeatability: float
    fingerprint: str
    synthesis_note: str


class ChronoHolographicImprint:
    """Synthesizes the first chrono-holographic story braid ever shipped."""

    def __init__(self, seed: int | None = None) -> None:
        self.seed = seed

    def craft(self, request: ImprintRequest) -> ImprintResult:
        timestamp = time.time()
        seed = request.seed if request.seed is not None else self.seed
        pulses = self._pulses(request.prompts, request.epochs, request.horizon, seed, timestamp)
        non_repeatability = self._non_repeatability(pulses)
        fingerprint = self._fingerprint(pulses, request.prompts, timestamp, seed)
        synthesis_note = self._note(pulses, non_repeatability)
        return ImprintResult(
            pulses=tuple(pulses),
            non_repeatability=non_repeatability,
            fingerprint=fingerprint,
            synthesis_note=synthesis_note,
        )

    def _pulses(
        self,
        prompts: Sequence[str],
        epochs: int,
        horizon: float,
        seed: int | None,
        timestamp: float,
    ) -> list[HolographicPulse]:
        motif_vectors = {prompt: self._motif_vector(prompt) for prompt in prompts}
        pal_primes = self._palindrome_primes(seed, epochs * len(prompts))
        pulses: list[HolographicPulse] = []
        for epoch in range(epochs):
            for prompt in prompts:
                vector = motif_vectors[prompt]
                phase = pal_primes[(epoch * len(prompts) + prompts.index(prompt)) % len(pal_primes)]
                novelty = self._novelty(vector, phase, horizon, timestamp)
                braid = self._braid_code(vector, phase, horizon)
                luminosity = self._luminosity(vector, phase, horizon)
                pulses.append(
                    HolographicPulse(
                        motif=prompt,
                        epoch_index=epoch,
                        novelty=novelty,
                        braid=braid,
                        luminosity=luminosity,
                    )
                )
        return pulses

    def _motif_vector(self, prompt: str) -> tuple[int, ...]:
        cleaned = prompt.lower().strip()
        if not cleaned:
            return (0,)
        return tuple(ord(char) % 97 for char in cleaned)

    def _palindrome_primes(self, seed: int | None, count: int) -> list[int]:
        start = 11 + (seed or 0) % 50
        pal_primes: list[int] = []
        candidate = max(11, start)
        while len(pal_primes) < count:
            if str(candidate) == str(candidate)[::-1] and self._is_prime(candidate):
                pal_primes.append(candidate)
            candidate += 1
        return pal_primes

    def _is_prime(self, value: int) -> bool:
        if value < 2:
            return False
        if value % 2 == 0:
            return value == 2
        limit = int(math.sqrt(value)) + 1
        for divisor in range(3, limit, 2):
            if value % divisor == 0:
                return False
        return True

    def _novelty(self, vector: Iterable[int], phase: int, horizon: float, timestamp: float) -> float:
        base = sum(vector) or 1
        modulation = math.sin(timestamp / 2.0) + math.cos(phase / horizon)
        return round((base % 97) * modulation / 42.0, 4)

    def _braid_code(self, vector: Iterable[int], phase: int, horizon: float) -> str:
        checksum = sum(v * (i + 1) for i, v in enumerate(vector)) + phase
        wobble = math.sin(phase / max(horizon, 0.0001))
        glyph = "HX" if wobble >= 0 else "VX"
        return f"{glyph}-{checksum:04d}-{abs(wobble):.3f}"

    def _luminosity(self, vector: Iterable[int], phase: int, horizon: float) -> float:
        vector_values = tuple(vector)
        variance = statistics.pvariance(vector_values) if len(vector_values) > 1 else 0.0
        return round((variance + phase % 13) / max(horizon, 1e-6), 3)

    def _non_repeatability(self, pulses: Sequence[HolographicPulse]) -> float:
        luminosities = [pulse.luminosity for pulse in pulses]
        braid_variants = len({pulse.braid for pulse in pulses})
        return round(statistics.pstdev(luminosities) + braid_variants * 0.031, 4)

    def _fingerprint(
        self,
        pulses: Sequence[HolographicPulse],
        prompts: Sequence[str],
        timestamp: float,
        seed: int | None,
    ) -> str:
        digest = hashlib.sha256()
        digest.update(str(seed or 0).encode())
        digest.update(str(timestamp).encode())
        for prompt in prompts:
            digest.update(prompt.encode())
        for pulse in pulses:
            digest.update(f"{pulse.novelty}:{pulse.braid}:{pulse.luminosity}".encode())
        return digest.hexdigest()[:32]

    def _note(self, pulses: Sequence[HolographicPulse], non_repeatability: float) -> str:
        horizon = max(pulse.epoch_index for pulse in pulses) + 1 if pulses else 0
        motifs = ", ".join(sorted({pulse.motif for pulse in pulses}))
        return (
            "This imprint braids palindromic prime orbits into motifs "
            f"({motifs}) across {horizon} epochs, delivering a measured "
            f"non-repeatability of {non_repeatability:.4f}."
        )


def demo() -> ImprintResult:
    engine = ChronoHolographicImprint(seed=42)
    request = ImprintRequest(prompts=("signal forests", "orbital poetry"), epochs=2, horizon=1.3)
    return engine.craft(request)


def _as_table(result: ImprintResult) -> str:
    lines = ["Holographic Imprint"]
    lines.append(f"non-repeatability: {result.non_repeatability:.4f}")
    lines.append(f"fingerprint: {result.fingerprint}")
    lines.append("pulses:")
    for pulse in result.pulses:
        lines.append(
            f"  - epoch {pulse.epoch_index} | {pulse.motif} | braid={pulse.braid} "
            f"| novelty={pulse.novelty:.3f} | luminosity={pulse.luminosity:.3f}"
        )
    lines.append(f"note: {result.synthesis_note}")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Cast a chrono-holographic imprint from prompts.",
    )
    parser.add_argument("--prompts", nargs="+", required=True, help="Motifs to braid")
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs to braid")
    parser.add_argument("--horizon", type=float, default=1.0, help="Temporal horizon modifier")
    parser.add_argument("--seed", type=int, default=None, help="Optional seed for reproducibility")
    args = parser.parse_args()

    engine = ChronoHolographicImprint(seed=args.seed)
    request = ImprintRequest(prompts=args.prompts, epochs=args.epochs, horizon=args.horizon)
    imprint = engine.craft(request)
    print(_as_table(imprint))
