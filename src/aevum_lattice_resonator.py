"""
Aevum Lattice Resonator – the first "chronicle braid" that weaves
prime harmonics, phyllotaxis, and mirrored narrative seeds into a
single time-aware signature.

Unlike ordinary text combiners, the resonator layers three distinct
signals:
* a prime stream (irreducible rhythm)
* a golden-ratio spiral (irrational drift)
* a palindromic seed echo (memory symmetry)

The result is a lattice signature that can be replayed, inspected, and
shared across creative systems while preserving the originating seeds
as a reversible breadcrumb trail.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Sequence


@dataclass
class AevumLatticeSignature:
    """Container for the resonator output.

    Attributes:
        chronicle_wave: Floating point phases keyed to each seed.
        palindrome_spine: Forward-and-backward echo of the input seeds.
        glyph_wave: Visual glyph braid rendered from primes and phases.
    """

    chronicle_wave: Dict[str, float]
    palindrome_spine: str
    glyph_wave: str


@dataclass
class AevumLatticeResonator:
    """World-first chronicle braid synthesizer.

    The resonator fuses prime rhythm, golden-ratio drift, and mirrored
    seeds into a glyph wave that can be embedded in manifests or logs.

    Args:
        seeds: Iterable of seed strings to braid.
        beat: Number of prime pulses to allocate per seed.
        spiral_ratio: Phyllotaxis-like ratio that drives the drift layer.
    """

    seeds: Iterable[str]
    beat: int = 3
    spiral_ratio: float = 0.618
    _seed_cache: List[str] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self._seed_cache = [seed.strip() for seed in self.seeds if seed.strip()]
        if not self._seed_cache:
            raise ValueError("At least one non-empty seed is required for resonance.")
        if self.beat < 1:
            raise ValueError("Beat must be positive to produce a lattice signature.")

    def _prime_stream(self) -> Iterator[int]:
        """Infinitely yields prime numbers for the rhythm layer."""

        n = 2
        while True:
            if all(n % p for p in range(2, int(math.sqrt(n)) + 1)):
                yield n
            n += 1

    def _phase_value(self, index: int, seed: str) -> float:
        drift = (index + 1) * self.spiral_ratio
        harmonic = (len(seed) + index * 3) / (sum(map(len, self._seed_cache)) or 1)
        phase = (drift + harmonic) % 1
        return round(phase, 6)

    def _glyph_for_seed(self, seed: str, primes: Sequence[int]) -> str:
        """Returns a compact glyph braid for one seed."""

        signature = []
        phase = self._phase_value(0, seed)
        for idx, prime in enumerate(primes):
            accent = "✶" if prime % 5 == 0 else "✹"
            phase = self._phase_value(idx, seed)
            signature.append(f"{accent}{prime % 10}:{phase:.3f}")
        seed_echo = f"⟲{seed[::-1]}⟳"
        return "|".join(signature + [seed_echo])

    def _palindrome_spine(self) -> str:
        forward = " · ".join(self._seed_cache)
        backward = " · ".join(reversed(self._seed_cache))
        return f"{forward} ⇋ {backward}"

    def resonate(self) -> AevumLatticeSignature:
        """Generates the lattice signature for the configured seeds."""

        prime_iter = self._prime_stream()
        chronicle_wave: Dict[str, float] = {}
        glyph_segments: List[str] = []

        for seed_index, seed in enumerate(self._seed_cache):
            prime_slice = list(itertools.islice(prime_iter, self.beat))
            chronicle_wave[seed] = self._phase_value(seed_index, seed)
            glyph_segments.append(self._glyph_for_seed(seed, prime_slice))

        glyph_wave = " || ".join(glyph_segments)
        palindrome_spine = self._palindrome_spine()
        return AevumLatticeSignature(
            chronicle_wave=chronicle_wave,
            palindrome_spine=palindrome_spine,
            glyph_wave=glyph_wave,
        )

    def render(self) -> str:
        """Pretty-print the lattice signature as multiline text."""

        signature = self.resonate()
        wave_lines = [f"• {seed}: phase {phase:.3f}" for seed, phase in signature.chronicle_wave.items()]
        return (
            "Aevum Lattice Signature\n"
            + "\n".join(wave_lines)
            + "\nSpine: "
            + signature.palindrome_spine
            + "\nGlyph Wave: "
            + signature.glyph_wave
        )


def demo() -> str:
    """Showcases the chronicle braid concept with three archetypal seeds."""

    seeds = ["Echo", "Asterion", "Mycelia"]
    resonator = AevumLatticeResonator(seeds=seeds, beat=4)
    return resonator.render()
