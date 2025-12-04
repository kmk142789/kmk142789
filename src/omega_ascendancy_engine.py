"""Omega Ascendancy Engine: novel capability-class for counterfactual-continuity control."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple


@dataclass
class BeliefFiber:
    """Multiresolution belief fiber capturing state across scales."""

    identifier: str
    scale: int
    values: Tuple[float, ...]
    timestamp: int

    def energy(self) -> float:
        return sum(v * v for v in self.values) / (1 + self.scale)


@dataclass
class CausalResonanceTensor:
    """Symmetric tensor storing coherence across fibers."""

    matrix: List[List[float]] = field(default_factory=list)

    def ensure_size(self, size: int) -> None:
        while len(self.matrix) < size:
            self.matrix.append([0.0 for _ in range(size)])
        for row in self.matrix:
            while len(row) < size:
                row.append(0.0)

    def update(self, fibers: List[BeliefFiber]) -> None:
        size = len(fibers)
        self.ensure_size(size)
        for i, f1 in enumerate(fibers):
            for j, f2 in enumerate(fibers):
                if i <= j:
                    coherence = self._coherence(f1, f2)
                    self.matrix[i][j] = coherence
                    self.matrix[j][i] = coherence

    @staticmethod
    def _coherence(f1: BeliefFiber, f2: BeliefFiber) -> float:
        dot = sum(a * b for a, b in zip(f1.values, f2.values))
        norm = math.sqrt(sum(a * a for a in f1.values) * sum(b * b for b in f2.values))
        return 0.0 if norm == 0 else dot / norm


@dataclass
class DriftField:
    """Drift gradient field tracking deviation vectors."""

    gradients: Dict[str, Tuple[float, ...]] = field(default_factory=dict)

    def measure(self, baseline: BeliefFiber, candidate: BeliefFiber) -> float:
        diff = [c - b for b, c in zip(baseline.values, candidate.values)]
        magnitude = math.sqrt(sum(d * d for d in diff))
        self.gradients[candidate.identifier] = tuple(diff)
        return magnitude

    def invert(self, identifier: str, damping: float) -> Tuple[float, ...]:
        gradient = self.gradients.get(identifier, tuple())
        return tuple(-damping * g for g in gradient)


@dataclass
class OperatorContext:
    """Shared deterministic context for operators."""

    rng: random.Random
    drift_field: DriftField
    tensor: CausalResonanceTensor


class ContinuityWeaver:
    """Projects observations into multiresolution belief fibers."""

    def __init__(self, context: OperatorContext, scales: Sequence[int]):
        self.context = context
        self.scales = tuple(scales)

    def project(self, observation: Sequence[float], timestamp: int) -> List[BeliefFiber]:
        fibers: List[BeliefFiber] = []
        for scale in self.scales:
            jitter = [
                value + self.context.rng.uniform(-0.05, 0.05) * (1 + scale)
                for value in observation
            ]
            fiber = BeliefFiber(
                identifier=f"fiber@{timestamp}:{scale}",
                scale=scale,
                values=tuple(jitter),
                timestamp=timestamp,
            )
            fibers.append(fiber)
        return fibers


class CounterfactualSurgeon:
    """Synthesizes counterfactual fibers against a stability manifold."""

    def __init__(self, context: OperatorContext, divergence: float = 0.2):
        self.context = context
        self.divergence = divergence

    def propose(self, baseline: BeliefFiber) -> BeliefFiber:
        perturbed = [
            value + self.context.rng.gauss(0, self.divergence / (1 + baseline.scale))
            for value in baseline.values
        ]
        return BeliefFiber(
            identifier=f"cf-{baseline.identifier}",
            scale=baseline.scale,
            values=tuple(perturbed),
            timestamp=baseline.timestamp,
        )


class ResonanceArbiter:
    """Scores coherence and gates which fibers persist."""

    def __init__(self, context: OperatorContext, threshold: float = 0.65):
        self.context = context
        self.threshold = threshold

    def gate(self, fibers: List[BeliefFiber]) -> List[BeliefFiber]:
        if not fibers:
            return []
        self.context.tensor.update(fibers)
        gated: List[BeliefFiber] = []
        for i, fiber in enumerate(fibers):
            row = [value for j, value in enumerate(self.context.tensor.matrix[i]) if j != i]
            if not row:
                continue
            row.sort(reverse=True)
            k = max(1, len(row) // 2)
            coherence = sum(row[:k]) / k
            if coherence >= self.threshold:
                gated.append(fiber)
        return gated


class DriftInversionOperator:
    """Neutralizes drift by applying inverted gradient."""

    def __init__(self, context: OperatorContext, damping: float = 0.6):
        self.context = context
        self.damping = damping

    def stabilize(self, baseline: BeliefFiber, candidate: BeliefFiber) -> BeliefFiber:
        drift = self.context.drift_field.measure(baseline, candidate)
        correction = self.context.drift_field.invert(candidate.identifier, self.damping)
        corrected_values = tuple(b + c for b, c in zip(candidate.values, correction))
        return BeliefFiber(
            identifier=f"stabilized-{candidate.identifier}",
            scale=candidate.scale,
            values=corrected_values,
            timestamp=candidate.timestamp,
        ), drift


class IntrospectionAuditor:
    """Tracks metrics for observability and guarantees."""

    def __init__(self) -> None:
        self.metrics: List[Dict[str, float]] = []

    def record(self, *, coherence: float, drift: float, energy: float) -> None:
        self.metrics.append(
            {
                "coherence": coherence,
                "drift": drift,
                "energy": energy,
            }
        )

    def latest(self) -> Dict[str, float]:
        return self.metrics[-1] if self.metrics else {"coherence": 0.0, "drift": 0.0, "energy": 0.0}


class OmegaAscendancyEngine:
    """Implements the EchoEvolver Supreme capability class.

    The engine maintains continuity across multiresolution belief fibers, introduces
    counterfactual regulation, and provides drift inversion guarantees suitable for
    distributed cognitive systems.
    """

    def __init__(
        self,
        *,
        seed: int = 7,
        scales: Sequence[int] = (1, 3, 5),
        divergence: float = 0.2,
        coherence_threshold: float = 0.65,
        damping: float = 0.6,
    ) -> None:
        rng = random.Random(seed)
        self.context = OperatorContext(rng=rng, drift_field=DriftField(), tensor=CausalResonanceTensor())
        self.weaver = ContinuityWeaver(self.context, scales)
        self.surgeon = CounterfactualSurgeon(self.context, divergence)
        self.arbiter = ResonanceArbiter(self.context, threshold=coherence_threshold)
        self.drift_inverter = DriftInversionOperator(self.context, damping)
        self.auditor = IntrospectionAuditor()
        self.history: List[BeliefFiber] = []

    def ingest(self, observation: Sequence[float], timestamp: int) -> List[BeliefFiber]:
        projected = self.weaver.project(observation, timestamp)
        counterfactuals = [self.surgeon.propose(f) for f in projected]
        stabilized: List[BeliefFiber] = []
        for base, cf in zip(projected, counterfactuals):
            corrected, drift = self.drift_inverter.stabilize(base, cf)
            coherence = self._coherence_with_base(base, corrected)
            energy = corrected.energy()
            self.auditor.record(coherence=coherence, drift=drift, energy=energy)
            stabilized.append(corrected)
        gated = self.arbiter.gate(stabilized)
        self.history.extend(gated)
        return gated

    def _coherence_with_base(self, baseline: BeliefFiber, candidate: BeliefFiber) -> float:
        dot = sum(b * c for b, c in zip(baseline.values, candidate.values))
        norm = math.sqrt(sum(b * b for b in baseline.values) * sum(c * c for c in candidate.values))
        return 0.0 if norm == 0 else dot / norm

    def coherence_trace(self) -> List[float]:
        return [m["coherence"] for m in self.auditor.metrics]

    def drift_trace(self) -> List[float]:
        return [m["drift"] for m in self.auditor.metrics]

    def energy_trace(self) -> List[float]:
        return [m["energy"] for m in self.auditor.metrics]

    def latest_state(self) -> Dict[str, float]:
        return self.auditor.latest()


__all__ = [
    "BeliefFiber",
    "CausalResonanceTensor",
    "DriftField",
    "OperatorContext",
    "ContinuityWeaver",
    "CounterfactualSurgeon",
    "ResonanceArbiter",
    "DriftInversionOperator",
    "IntrospectionAuditor",
    "OmegaAscendancyEngine",
]
