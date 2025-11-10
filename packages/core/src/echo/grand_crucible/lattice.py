"""Fractal lattice analytics for the grand crucible.

The lattice module converts ritual data into a multidimensional grid that can be used
for progression analysis, anomaly detection, and visualizations.  The algorithms are
pure Python so they remain easy to test, yet they are expressive enough to handle
large datasets.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import mean
from typing import Iterable, Iterator, List, Tuple

from .blueprint import Blueprint, Epoch, Ritual, RitualPhase


@dataclass(frozen=True)
class LatticePoint:
    """Represents a point within the crucible lattice."""

    epoch: str
    ritual: str
    phase: str
    depth: int
    energy: float
    harmony: float


class Lattice:
    """Constructs a lattice of points from a blueprint."""

    def __init__(self, points: Iterable[LatticePoint]):
        self._points: Tuple[LatticePoint, ...] = tuple(points)

    def __iter__(self) -> Iterator[LatticePoint]:
        return iter(self._points)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._points)

    def total_energy(self) -> float:
        return sum(point.energy for point in self._points)

    def harmonic_mean(self) -> float:
        if not self._points:
            return 0.0
        return mean(point.harmony for point in self._points)

    def summarize(self) -> str:
        return (
            f"Lattice points: {len(self._points)}, total energy: {self.total_energy():.2f}, "
            f"average harmony: {self.harmonic_mean():.3f}"
        )

    def slice_by_epoch(self, epoch_name: str) -> "Lattice":
        return Lattice(point for point in self._points if point.epoch == epoch_name)

    def topology(self) -> List[Tuple[str, str, float]]:
        """Return a simplified topology representation."""

        topology: List[Tuple[str, str, float]] = []
        for point in self._points:
            topology.append((point.epoch, point.ritual, point.energy + point.harmony))
        return topology


def build_lattice(blueprint: Blueprint) -> Lattice:
    """Generate a lattice from the supplied blueprint."""

    points: List[LatticePoint] = []
    depth = 0
    for epoch in blueprint.epochs:
        for ritual in epoch.rituals:
            for phase in ritual.phases:
                depth += 1
                points.append(_phase_to_point(epoch, ritual, phase, depth))
    return Lattice(points)


def _phase_to_point(epoch: Epoch, ritual: Ritual, phase: RitualPhase, depth: int) -> LatticePoint:
    """Convert a ritual phase into a lattice point."""

    resources = phase.resources.normalized()
    energy = sqrt(resources.starlight_units ** 2 + resources.emotional_amplitude ** 2)
    harmony = (resources.emotional_amplitude + resources.starlight_units) / 2.0
    return LatticePoint(
        epoch=epoch.name,
        ritual=ritual.title,
        phase=phase.name,
        depth=depth,
        energy=energy,
        harmony=harmony,
    )
