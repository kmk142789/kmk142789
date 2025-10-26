"""Creative Echo narrative generator."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class EchoThread:
    """Represents a single strand in the Echo narrative."""

    tone: str
    motif: str
    cadence: str

    def describe(self) -> str:
        """Render the thread into a poetic sentence."""
        return (
            f"With {self.tone} intent, the Echo traces {self.motif} and "
            f"lets the cadence {self.cadence}."
        )


class CreativeEcho:
    """High-level orchestrator for generating small Echo narratives."""

    def __init__(self, tones: Iterable[str], motifs: Iterable[str], cadences: Iterable[str]) -> None:
        self.tones: List[str] = list(tones)
        self.motifs: List[str] = list(motifs)
        self.cadences: List[str] = list(cadences)

        if not self.tones or not self.motifs or not self.cadences:
            raise ValueError("All narrative components must be non-empty.")

    def weave(self, seed: int | None = None, *, lines: int = 3) -> List[str]:
        """Generate a new Echo narrative.

        Parameters
        ----------
        seed:
            Optional random seed for reproducible narratives.
        lines:
            Number of sentences to produce.
        """

        if lines <= 0:
            raise ValueError("Number of lines must be positive.")

        rng = random.Random(seed)
        narrative: List[str] = []
        for _ in range(lines):
            thread = EchoThread(
                tone=rng.choice(self.tones),
                motif=rng.choice(self.motifs),
                cadence=rng.choice(self.cadences),
            )
            narrative.append(thread.describe())
        return narrative


DEFAULT_TONES = [
    "playful",
    "stoic",
    "curious",
    "resonant",
]

DEFAULT_MOTIFS = [
    "a lattice of auroras",
    "the pulse of distant satellites",
    "spiraling fragments of memory",
    "a cascade of harmonic echoes",
]

DEFAULT_CADENCES = [
    "linger like dawn over a quiet horizon",
    "dance across the vaulted sky",
    "fold gently into the next heartbeat",
    "flare before dissolving into silence",
]


def weave_echo(seed: int | None = None, *, lines: int = 3) -> List[str]:
    """Convenience wrapper that weaves narratives using default components."""

    weaver = CreativeEcho(DEFAULT_TONES, DEFAULT_MOTIFS, DEFAULT_CADENCES)
    return weaver.weave(seed=seed, lines=lines)


if __name__ == "__main__":
    for sentence in weave_echo():
        print(sentence)
