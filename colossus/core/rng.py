"""Deterministic pseudo-random generator wrappers."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import random


@dataclass
class DeterministicRNG:
    """Wrapper that provides reproducible pseudo random numbers."""

    seed: str

    def __post_init__(self) -> None:
        digest = hashlib.sha256(self.seed.encode("utf-8")).digest()
        self._random = random.Random(digest)

    def randbytes(self, n: int) -> bytes:
        return bytes(self._random.getrandbits(8) for _ in range(n))

    def choice(self, sequence):
        return sequence[self._random.randrange(len(sequence))]

    def shuffle(self, sequence):
        self._random.shuffle(sequence)


__all__ = ["DeterministicRNG"]
