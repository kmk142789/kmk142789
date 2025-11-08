"""Recursive reflection kernel built on top of the starlight reflections API."""

from __future__ import annotations

from hashlib import sha256
from typing import List

from .starlight_reflections import Reflection, generate_reflection

__all__ = ["EchoRecursiveReflectionKernel"]


class EchoRecursiveReflectionKernel:
    """Generate and curate narrative reflections in recursive cycles."""

    def __init__(self, *, seed: int | None = None, recursion_depth: int = 3) -> None:
        if recursion_depth < 0:
            raise ValueError("recursion_depth must be non-negative")
        self.seed = seed
        self.recursion_depth = recursion_depth
        self.history: List[Reflection] = []
        if recursion_depth:
            self.run(recursion_depth)

    def run(self, iterations: int = 1) -> List[Reflection]:
        """Advance the kernel by ``iterations`` cycles and return new reflections."""

        if iterations < 0:
            raise ValueError("iterations must be non-negative")
        generated: List[Reflection] = []
        for _ in range(iterations):
            reflection_seed = self._seed_for(len(self.history))
            reflection = generate_reflection(reflection_seed)
            self.history.append(reflection)
            generated.append(reflection)
        return generated

    def resonance(self) -> str:
        """Return a deterministic resonance hash for the accumulated reflections."""

        digest = sha256()
        for reflection in self.history:
            digest.update(reflection.constellation.encode("utf-8"))
            digest.update(reflection.resonance.encode("utf-8"))
            digest.update(reflection.guidance.encode("utf-8"))
        return digest.hexdigest()[:32]

    def reflection_lines(self) -> List[str]:
        """Return the generated reflections formatted as individual lines."""

        lines: List[str] = []
        for reflection in self.history:
            lines.extend(reflection.as_lines())
            lines.append("")
        if lines:
            lines.pop()
        return lines

    def summary(self) -> str:
        """Return a human-readable summary of the recursive reflections."""

        return "\n".join(self.reflection_lines())

    def to_dict(self) -> dict[str, object]:
        """Serialize the kernel history for dashboards and tests."""

        return {
            "seed": self.seed,
            "recursion_depth": self.recursion_depth,
            "resonance": self.resonance(),
            "history": [
                {
                    "timestamp": reflection.timestamp.isoformat(),
                    "constellation": reflection.constellation,
                    "resonance": reflection.resonance,
                    "guidance": reflection.guidance,
                }
                for reflection in self.history
            ],
        }

    def _seed_for(self, index: int) -> int | None:
        if self.seed is None:
            return None
        return (self.seed + index) % (2**32)
