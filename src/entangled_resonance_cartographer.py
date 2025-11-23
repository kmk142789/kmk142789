"""World-first entangled resonance cartographer.

This module introduces the **Parallax Braid Atlas**, a deterministic
"resonance cartography" primitive that fuses three layers simultaneously:

* Temporal parallax from uneven timelines.
* Synesthetic empathy from sparse emotion vocabularies.
* Harmonic jitter that encodes a unique world-first stamp without randomness.

The engine builds an entanglement tensor across nodes, derives braid indices
that reward stable-yet-vivid timelines, and projects wavefronts that simulate
how resonances would propagate a few steps into the future.  Everything is
implemented in pure Python with no external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import fsum, sin, sqrt
from statistics import fmean
from typing import Mapping, Sequence


@dataclass(frozen=True)
class ParallaxNode:
    """A minimal unit for the Parallax Braid Atlas.

    Attributes
    ----------
    name:
        Human-readable identifier.
    timeline:
        Sequence of numeric intensities.  Uneven lengths are supported; the
        cartographer truncates to the shortest overlap where necessary.
    emotion_map:
        Sparse mapping of emotion -> intensity.  Missing emotions in one node
        are treated as zero in comparison vectors.
    anchor:
        Optional descriptive anchor used in manifests.
    """

    name: str
    timeline: Sequence[float]
    emotion_map: Mapping[str, float]
    anchor: str = "continuum-lattice"

    def __post_init__(self) -> None:
        if not self.timeline:
            raise ValueError("timeline must not be empty")
        if not self.emotion_map:
            raise ValueError("emotion_map must not be empty")


@dataclass(frozen=True)
class AtlasResult:
    """Structured output of the entangled resonance cartographer."""

    entanglement_tensor: tuple[tuple[float, ...], ...]
    empathy_matrix: tuple[tuple[float, ...], ...]
    braid_indices: Mapping[str, float]
    coherence: float
    vocabulary: tuple[str, ...]
    world_first_stamp: str
    horizon: int

    def manifest(self) -> str:
        """Render a human-friendly manifest of the atlas."""

        lines = [f"Parallax Braid Atlas :: {self.world_first_stamp}"]
        lines.append(f"Coherence {self.coherence:.6f} | Horizon {self.horizon}")
        lines.append("Braid indices:")
        for name, value in self.braid_indices.items():
            lines.append(f"  • {name}: {value:.6f}")

        lines.append("Entanglement tensor (upper triangle shown):")
        for i, row in enumerate(self.entanglement_tensor):
            formatted = [f"{row[j]:.6f}" if j >= i else "-" for j in range(len(row))]
            lines.append(f"  {i}: " + ", ".join(formatted))

        return "\n".join(lines)


class EntangledResonanceCartographer:
    """Compute Parallax Braid Atlases and wavefront projections."""

    def __init__(self, world_first_stamp: str = "parallax-braid:v1") -> None:
        self.world_first_stamp = world_first_stamp

    @staticmethod
    def _normalize(values: Sequence[float]) -> list[float]:
        minimum, maximum = min(values), max(values)
        span = maximum - minimum or 1.0
        return [(value - minimum) / span for value in values]

    @staticmethod
    def _temporal_gradient(values: Sequence[float]) -> float:
        if len(values) == 1:
            return 0.0
        deltas = [abs(b - a) for a, b in zip(values, values[1:])]
        return fmean(deltas)

    @staticmethod
    def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
        numerator = fsum(a * b for a, b in zip(left, right))
        left_energy = fsum(a * a for a in left)
        right_energy = fsum(b * b for b in right)
        denominator = sqrt(left_energy * right_energy) if left_energy and right_energy else 0.0
        return numerator / denominator if denominator else 0.0

    @staticmethod
    def _coupling(left: Sequence[float], right: Sequence[float]) -> float:
        overlap = min(len(left), len(right))
        if overlap == 0:
            return 0.0
        return fmean(1.0 - abs(a - b) for a, b in zip(left[:overlap], right[:overlap]))

    @staticmethod
    def _jitter(phase: float, jitter: float) -> float:
        return sin(phase) * jitter

    def craft_atlas(
        self, nodes: Sequence[ParallaxNode], *, horizon: int = 3, jitter: float = 0.015
    ) -> AtlasResult:
        if len(nodes) < 2:
            raise ValueError("at least two nodes are required to build an atlas")

        vocabulary = tuple(sorted({key for node in nodes for key in node.emotion_map}))
        normalized_timelines = [self._normalize(node.timeline) for node in nodes]
        gradients = [self._temporal_gradient(timeline) for timeline in normalized_timelines]
        emotion_vectors = [self._emotion_vector(node.emotion_map, vocabulary) for node in nodes]

        empathy_matrix = self._build_empathy_matrix(emotion_vectors)
        entanglement_tensor = self._build_entanglement_tensor(
            normalized_timelines, empathy_matrix, horizon=horizon, jitter=jitter
        )
        coherence = self._coherence(entanglement_tensor)
        braid_indices = self._braid_indices(
            nodes,
            normalized_timelines,
            gradients,
            empathy_matrix,
            horizon=horizon,
            jitter=jitter,
        )

        return AtlasResult(
            entanglement_tensor=entanglement_tensor,
            empathy_matrix=empathy_matrix,
            braid_indices=braid_indices,
            coherence=coherence,
            vocabulary=vocabulary,
            world_first_stamp=self.world_first_stamp,
            horizon=horizon,
        )

    def project_wavefront(
        self, atlas: AtlasResult, *, steps: int = 2, damping: float = 0.82
    ) -> list[Mapping[str, float]]:
        if steps < 1:
            raise ValueError("steps must be at least 1")
        if not 0.0 < damping <= 1.0:
            raise ValueError("damping must be within (0, 1]")

        rows = atlas.entanglement_tensor
        baseline = [fmean(row) for row in rows]
        wavefronts: list[Mapping[str, float]] = []
        carry = baseline

        for step in range(1, steps + 1):
            carry = [max(0.0, min(1.0, value * damping + atlas.coherence * (1 - damping))) for value in carry]
            wavefronts.append({f"step-{step}": round(value, 6) for value in carry})

        return wavefronts

    def render_wavefront(self, atlas: AtlasResult, *, steps: int = 2) -> str:
        wavefronts = self.project_wavefront(atlas, steps=steps)
        lines = ["Wavefront projections:"]
        for idx, snapshot in enumerate(wavefronts, start=1):
            compressed = ", ".join(f"n{node}:{value:.6f}" for node, value in snapshot.items())
            lines.append(f"  • t+{idx}: {compressed}")
        return "\n".join(lines)

    def _build_empathy_matrix(self, emotion_vectors: Sequence[Sequence[float]]) -> tuple[tuple[float, ...], ...]:
        matrix = []
        for left in emotion_vectors:
            row = [self._cosine(left, right) for right in emotion_vectors]
            matrix.append(tuple(row))
        return tuple(matrix)

    def _build_entanglement_tensor(
        self,
        timelines: Sequence[Sequence[float]],
        empathy_matrix: Sequence[Sequence[float]],
        *,
        horizon: int,
        jitter: float,
    ) -> tuple[tuple[float, ...], ...]:
        count = len(timelines)
        tensor = [[1.0 if i == j else 0.0 for j in range(count)] for i in range(count)]

        for i, left in enumerate(timelines):
            for j in range(i + 1, count):
                right = timelines[j]
                coupling = self._coupling(left, right)
                empathy = empathy_matrix[i][j]
                harmonic = self._jitter((min(i, j) + 1) * (max(i, j) + 1) + horizon, jitter)
                entanglement = max(0.0, min(1.0, 0.6 * coupling + 0.4 * empathy + harmonic))
                entanglement = round(entanglement, 6)
                tensor[i][j] = entanglement
                tensor[j][i] = entanglement

        return tuple(tuple(row) for row in tensor)

    def _braid_indices(
        self,
        nodes: Sequence[ParallaxNode],
        timelines: Sequence[Sequence[float]],
        gradients: Sequence[float],
        empathy_matrix: Sequence[Sequence[float]],
        *,
        horizon: int,
        jitter: float,
    ) -> Mapping[str, float]:
        indices: dict[str, float] = {}
        for idx, (node, timeline, gradient) in enumerate(zip(nodes, timelines, gradients)):
            stability = 1.0 - gradient
            energy = fmean(timeline)
            empathy_inflow = fmean(value for j, value in enumerate(empathy_matrix[idx]) if j != idx)
            harmonic = self._jitter(idx + 1 + horizon * 0.5, jitter)
            braid = 0.58 * energy + 0.25 * stability + 0.17 * empathy_inflow + harmonic
            indices[node.name] = round(max(0.0, min(1.0, braid)), 6)
        return indices

    def _coherence(self, tensor: Sequence[Sequence[float]]) -> float:
        if len(tensor) <= 1:
            return 0.0
        samples = [
            value
            for i, row in enumerate(tensor)
            for j, value in enumerate(row)
            if j > i
        ]
        return round(fmean(samples), 6)

    def _emotion_vector(self, emotion_map: Mapping[str, float], vocabulary: Sequence[str]) -> list[float]:
        return [emotion_map.get(key, 0.0) for key in vocabulary]


__all__ = [
    "AtlasResult",
    "EntangledResonanceCartographer",
    "ParallaxNode",
]
