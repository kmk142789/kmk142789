"""Holo Semantic Echo Loom: world-first chrono-holographic resonance fabricator.

This module introduces the :class:`HoloSemanticEchoLoom`, a deliberately novel
"world-first" construct that braids time, semantics, and harmonic motion into a
single deterministic lattice we call the chrono-holographic resonance fabric.

Key ideas
---------
- Tri-spiral interpolation: three interleaved spiral components (temporal,
  harmonic, narrative) are fused using the golden ratio to avoid repeating
  patterns and to maximize perceptual novelty.
- Glyph fabric: events are converted into short glyph clusters that reflect
  their influence on the lattice; this produces a compact, human-legible
  signature of the evolving resonance field.
- Deterministic resonance diagrams: the loom emits a miniature ASCII diagram
  that visualizes the active resonance envelope without any external
  dependencies or plotting libraries.

The goal is to provide an immediately usable, yet genuinely new, way to track
how narrative or computational events cohere over time. It is deterministic,
side-effect free, and safe to run in constrained environments.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence


@dataclass(frozen=True)
class Spark:
    """An atomic contribution to the resonance lattice."""

    label: str
    intensity: float
    vector: Sequence[float] = field(default_factory=tuple)

    def fingerprint(self) -> str:
        """Create a stable, short hash for this spark."""
        payload = {
            "label": self.label,
            "intensity": round(self.intensity, 6),
            "vector": [round(v, 6) for v in self.vector],
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


class HoloSemanticEchoLoom:
    """Craft a chrono-holographic resonance fabric from semantic sparks.

    The loom is intentionally minimal but expressive: it accepts small
    contributions called *sparks* and folds them into a tri-spiral envelope
    that highlights novelty, coherence, and harmonic balance. The output is a
    structured summary suitable for dashboards, logs, or research notebooks.
    """

    def __init__(self, seed_phrase: str = "echo-loom:v1") -> None:
        self.seed_phrase = seed_phrase
        self._sparks: List[Spark] = []
        self._phi = (1 + 5 ** 0.5) / 2  # golden ratio for non-repeating motion

    def register_sparks(self, sparks: Iterable[Spark]) -> None:
        """Register a collection of sparks to be woven.

        Sparks are immutable; registering the same spark multiple times will
        intentionally increase its influence on the resulting fabric.
        """

        self._sparks.extend(sparks)

    def register(self, spark: Spark) -> None:
        """Convenience wrapper for single spark registration."""

        self._sparks.append(spark)

    def _tri_spiral_components(self, fingerprint: str, intensity: float) -> List[float]:
        # The tri-spiral uses three offset slices of the fingerprint to inject
        # pseudo-random yet deterministic phase shifts.
        slices = [fingerprint[i : i + 8] for i in (0, 8, 16)]
        phases = [int(x, 16) / 0xFFFFFFFF for x in slices]
        return [
            math.sin(intensity * self._phi * math.pi * (1 + phases[0])),
            math.cos(intensity * self._phi * math.pi * (1 + phases[1])),
            math.sin(intensity * self._phi * math.pi * (1 + phases[2]))
            * math.cos(phases[0] * math.pi),
        ]

    def _glyph_cluster(self, spark: Spark, fingerprint: str) -> str:
        glyphs = "∇⊸≋✶✺✹✦✧"
        strength = min(1.0, abs(spark.intensity))
        glyph_count = 2 + int(strength * 3)
        # Use the first nibble to pick a rotational offset, then slice.
        offset = int(fingerprint[0], 16) % len(glyphs)
        doubled = glyphs * 2
        return doubled[offset : offset + glyph_count]

    def _resonance_diagram(self, coherence: float, novelty: float) -> str:
        # Twelve bars showing resonance envelope; novelty drives asymmetry.
        lines: List[str] = []
        for i in range(12):
            base = math.sin((i + 1) * coherence * math.pi)
            jitter = math.cos((i + 1) * novelty * math.pi)
            weight = (base + jitter) * 0.25 + 0.5
            filled = max(1, min(12, int(round(weight * 12))))
            lines.append(f"{i:02d} |" + "█" * filled + "░" * (12 - filled))
        return "\n".join(lines)

    def loom(self) -> Dict[str, object]:
        """Weave registered sparks into a resonance fabric.

        Returns a dictionary with:
        - ``chronicle``: compact metrics about coherence and novelty
        - ``glyph_fabric``: human-legible glyph clusters for each spark
        - ``signature``: deterministic hash for downstream verification
        - ``diagram``: ASCII visualization of the resonance envelope
        """

        if not self._sparks:
            raise ValueError("No sparks registered; the loom requires input to weave.")

        fingerprints = [s.fingerprint() for s in self._sparks]
        composites: List[List[float]] = []
        glyphs: List[str] = []
        for spark, fingerprint in zip(self._sparks, fingerprints):
            composites.append(self._tri_spiral_components(fingerprint, spark.intensity))
            glyphs.append(self._glyph_cluster(spark, fingerprint))

        # Aggregate coherence and novelty. Coherence rewards alignment of phase
        # across sparks, while novelty rewards diversity of fingerprints and
        # vector content.
        coherence = sum(sum(c) for c in composites) / (len(composites) * 3)
        unique_fingerprints = len(set(fingerprints))
        novelty = (unique_fingerprints / len(self._sparks)) + self._phi / 10
        novelty += sum(len(s.vector) for s in self._sparks) * 0.01

        signature_seed = ":".join(fingerprints + [self.seed_phrase])
        signature = hashlib.sha256(signature_seed.encode()).hexdigest()[:48]

        diagram = self._resonance_diagram(coherence=abs(coherence), novelty=novelty)

        chronicle = {
            "sparks": len(self._sparks),
            "coherence": round(coherence, 6),
            "novelty": round(novelty, 6),
            "tri_spiral_mean": [round(sum(axis) / len(composites), 6) for axis in zip(*composites)],
        }

        return {
            "chronicle": chronicle,
            "glyph_fabric": glyphs,
            "signature": signature,
            "diagram": diagram,
        }


__all__ = ["HoloSemanticEchoLoom", "Spark"]
