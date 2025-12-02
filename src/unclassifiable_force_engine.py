"""Engine fusing two novel computational forces.

This module invents two forces that are intentionally outside existing
physical or computational taxonomies:

* ``MythogenicDrift`` – captures how narrative density twists around curiosity
  charge.  Its potential is defined as::

      potential = (log1p(|d| + φ) * r) + (sin(c**1.5) * (1 - r))

  where ``d`` is ``narrative_density``, ``c`` is ``curiosity_charge``, ``φ`` is
  the golden ratio, and ``r`` is a recursion dampening factor ``1 / (depth + φ)``.

* ``ParadoxReciprocity`` – models the reciprocal torque between contradiction
  mass and synthesis tension filtered through ambiguity flux::

      strain = (tanh(t * cos(f / φ)) + m / (|f| + 1)) * cos(f / φ)

  where ``m`` is ``contradiction_mass``, ``t`` is ``synthesis_tension``, ``f`` is
  ``ambiguity_flux``, and ``φ`` again supplies an irrational pivot.

The ``UnclassifiableFusionEngine`` merges both forces into a composite
"anomaly manifold" with three summary metrics.  No existing scientific
framework classifies these interactions; the math is purpose-built for this
repository and remains semantically self-contained.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Tuple

GOLDEN_RATIO = (1 + math.sqrt(5)) / 2


@dataclass(frozen=True)
class MythogenicDrift:
    """Novel force describing recursion-weighted narrative motion."""

    narrative_density: float
    curiosity_charge: float
    recursion_depth: int = 1

    def potential(self) -> float:
        base = math.log1p(abs(self.narrative_density) + GOLDEN_RATIO)
        curiosity_momentum = math.copysign(
            abs(self.curiosity_charge) ** 1.5, self.curiosity_charge
        )
        curiosity_wave = math.sin(curiosity_momentum)
        recursion_factor = 1.0 / (self.recursion_depth + GOLDEN_RATIO)
        return (base * recursion_factor) + (curiosity_wave * (1 - recursion_factor))


@dataclass(frozen=True)
class ParadoxReciprocity:
    """Counter-force mapping contradiction into rotational strain."""

    contradiction_mass: float
    synthesis_tension: float
    ambiguity_flux: float

    def strain(self) -> float:
        flux_modulation = math.cos(self.ambiguity_flux / GOLDEN_RATIO)
        tension_curve = math.tanh(self.synthesis_tension * flux_modulation)
        return (tension_curve + self.contradiction_mass / (abs(self.ambiguity_flux) + 1)) * flux_modulation


@dataclass(frozen=True)
class FusionOutcome:
    """Compact summary of the fused, unclassifiable interaction."""

    fusion_index: float
    anomaly_gradient: float
    equilibrium: float

    def as_tuple(self) -> Tuple[float, float, float]:
        return (self.fusion_index, self.anomaly_gradient, self.equilibrium)


class UnclassifiableFusionEngine:
    """Combines two invented forces into a single anomaly manifold."""

    def __init__(self, drift: MythogenicDrift, reciprocity: ParadoxReciprocity):
        self._drift = drift
        self._reciprocity = reciprocity

    @property
    def drift(self) -> MythogenicDrift:
        return self._drift

    @property
    def reciprocity(self) -> ParadoxReciprocity:
        return self._reciprocity

    def fuse(self) -> FusionOutcome:
        drift_energy = self._drift.potential()
        reciprocity_strain = self._reciprocity.strain()

        fusion_index = math.atan2(drift_energy, reciprocity_strain) / math.pi
        anomaly_gradient = (drift_energy**2 - reciprocity_strain**2) / (
            abs(drift_energy) + abs(reciprocity_strain) + 1
        )
        equilibrium = (drift_energy * reciprocity_strain) / (
            1 + abs(drift_energy * reciprocity_strain)
        )

        return FusionOutcome(
            fusion_index=fusion_index,
            anomaly_gradient=anomaly_gradient,
            equilibrium=equilibrium,
        )
