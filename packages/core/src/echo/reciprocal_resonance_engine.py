"""
Reciprocal Resonance Engine
---------------------------

This module introduces the Reciprocal Resonance Engine (RRE), a novel capability for
alignment-critical operations. The engine fuses multi-source signals, human or system
commitments, and time-sensitive outcomes into a reciprocal influence graph. The design is
rooted in cognitive systems principles (reciprocal determinism, predictive processing) and
computer science foundations (graph analytics, exponential decay windows, vector similarity).

The engine exposes three primitives:
- SignalEvent: structured, weighted observations from any subsystem.
- Commitment: intent-bearing predictions with temporal horizons.
- Resonance evaluation: Bidirectional Predictive Alignment (BPA), a new scoring mechanic
  that balances forward predictive accuracy, backward coverage, and lateral coherence across
  peer commitments.

The outputs include actionable intervention proposals and a machine-readable graph that can
be consumed by downstream visualization or orchestration layers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np


@dataclass
class SignalEvent:
    """Observation emitted by any subsystem.

    Attributes:
        source: Human or system origin of the event.
        timestamp: When the event was recorded.
        features: Metric map (e.g., {"latency_ms": 123}).
        confidence: Reporter trust weight in [0, 1].
    """

    source: str
    timestamp: datetime
    features: Dict[str, float]
    confidence: float = 1.0

    def normalized(self) -> "SignalEvent":
        bounded_confidence = min(1.0, max(0.0, self.confidence))
        return SignalEvent(
            source=self.source,
            timestamp=self.timestamp,
            features=self.features,
            confidence=bounded_confidence,
        )


@dataclass
class Commitment:
    """Intent-bearing prediction or policy from an actor.

    Attributes:
        actor: Agent or system publishing the commitment.
        intent: Natural-language description of the planned outcome.
        predicted_features: Expected metric deltas or values.
        horizon_seconds: Time until the commitment is expected to manifest.
        risk_tolerance: Higher values favor aggressive actions when alignment is marginal.
        weight: Influence of the actor in the collective negotiation.
    """

    actor: str
    intent: str
    predicted_features: Dict[str, float]
    horizon_seconds: float
    risk_tolerance: float = 0.5
    weight: float = 1.0


@dataclass
class ResonanceResult:
    """Alignment report produced by the engine."""

    commitment: Commitment
    forward_error: float
    backward_coverage: float
    lateral_coherence: float
    overall_score: float
    matched_features: Dict[str, Tuple[float, float]]
    recommendations: List[str] = field(default_factory=list)


class ReciprocalResonanceEngine:
    """Bidirectional Predictive Alignment (BPA) engine.

    BPA is new in that it explicitly measures:
    - Forward fidelity: How well observed signals match each commitment.
    - Backward coverage: How much of a commitment's predictive surface is explained by signals.
    - Lateral coherence: How compatible commitments are with one another (mutual predictability),
      enabling coalition-aware adjustments.
    """

    def __init__(
        self,
        decay_half_life_seconds: float = 900.0,
        coherence_floor: float = 0.15,
    ) -> None:
        self.decay_half_life_seconds = max(1.0, decay_half_life_seconds)
        self.coherence_floor = coherence_floor
        self.events: List[SignalEvent] = []
        self.commitments: List[Commitment] = []

    def ingest_event(self, event: SignalEvent) -> None:
        self.events.append(event.normalized())

    def register_commitment(self, commitment: Commitment) -> None:
        self.commitments.append(commitment)

    def _decay_weight(self, timestamp: datetime, now: datetime) -> float:
        age = max(0.0, (now - timestamp).total_seconds())
        return 0.5 ** (age / self.decay_half_life_seconds)

    def _aggregate_signals(self, now: Optional[datetime] = None) -> Dict[str, float]:
        now = now or datetime.now(timezone.utc)
        weighted_sum: Dict[str, float] = {}
        weight_total: Dict[str, float] = {}
        for event in self.events:
            weight = self._decay_weight(event.timestamp, now) * event.confidence
            for key, value in event.features.items():
                weighted_sum[key] = weighted_sum.get(key, 0.0) + value * weight
                weight_total[key] = weight_total.get(key, 0.0) + weight
        return {
            key: (weighted_sum[key] / weight_total[key])
            for key in weighted_sum
            if weight_total[key] > 0
        }

    @staticmethod
    def _feature_vector(keys: Iterable[str], mapping: Dict[str, float]) -> np.ndarray:
        return np.array([mapping.get(k, 0.0) for k in keys], dtype=float)

    @staticmethod
    def _cosine(a: np.ndarray, b: np.ndarray) -> float:
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)

    def _lateral_coherence(self) -> float:
        if len(self.commitments) < 2:
            return 1.0
        keys = sorted({k for c in self.commitments for k in c.predicted_features})
        vectors = [self._feature_vector(keys, c.predicted_features) for c in self.commitments]
        scores = []
        for i in range(len(vectors)):
            for j in range(i + 1, len(vectors)):
                scores.append(self._cosine(vectors[i], vectors[j]))
        return max(self.coherence_floor, float(np.mean(scores))) if scores else 1.0

    def evaluate(self, now: Optional[datetime] = None) -> List[ResonanceResult]:
        if not self.commitments:
            return []
        now = now or datetime.now(timezone.utc)
        aggregate = self._aggregate_signals(now)
        coherence = self._lateral_coherence()
        results: List[ResonanceResult] = []
        for commitment in self.commitments:
            matched = {
                k: (commitment.predicted_features[k], aggregate[k])
                for k in commitment.predicted_features.keys() & aggregate.keys()
            }
            forward_error = self._forward_error(commitment.predicted_features, aggregate)
            backward_coverage = (
                len(matched) / max(1, len(commitment.predicted_features))
            )
            overall = self._overall_score(
                forward_error=forward_error,
                backward_coverage=backward_coverage,
                coherence=coherence,
                risk_tolerance=commitment.risk_tolerance,
                weight=commitment.weight,
            )
            recommendations = self._recommendations(
                forward_error=forward_error,
                backward_coverage=backward_coverage,
                coherence=coherence,
                commitment=commitment,
            )
            results.append(
                ResonanceResult(
                    commitment=commitment,
                    forward_error=forward_error,
                    backward_coverage=backward_coverage,
                    lateral_coherence=coherence,
                    overall_score=overall,
                    matched_features=matched,
                    recommendations=recommendations,
                )
            )
        return sorted(results, key=lambda r: r.overall_score, reverse=True)

    def _forward_error(self, prediction: Dict[str, float], observation: Dict[str, float]) -> float:
        if not prediction:
            return 1.0
        overlapping = prediction.keys() & observation.keys()
        if not overlapping:
            return 1.0
        errors = []
        for key in overlapping:
            pred = prediction[key]
            obs = observation[key]
            denom = max(1e-9, abs(pred) + abs(obs))
            errors.append(abs(pred - obs) / denom)
        return float(np.clip(np.mean(errors), 0.0, 1.0))

    def _overall_score(
        self,
        *,
        forward_error: float,
        backward_coverage: float,
        coherence: float,
        risk_tolerance: float,
        weight: float,
    ) -> float:
        fidelity = 1.0 - forward_error
        coverage_component = backward_coverage
        coherence_component = coherence
        score = (
            0.45 * fidelity
            + 0.35 * coverage_component
            + 0.20 * coherence_component
        )
        adjusted = score * (0.5 + 0.5 * weight) * (0.9 + 0.2 * risk_tolerance)
        return float(np.clip(adjusted, 0.0, 1.0))

    def _recommendations(
        self,
        *,
        forward_error: float,
        backward_coverage: float,
        coherence: float,
        commitment: Commitment,
    ) -> List[str]:
        actions = []
        if forward_error > 0.35:
            actions.append(
                f"Tighten telemetry for {commitment.actor}: drift={forward_error:.2f}"
            )
        if backward_coverage < 0.5:
            missing = set(commitment.predicted_features) - set()
            actions.append(
                f"Instrument missing metrics for {commitment.actor}: {sorted(missing)}"
            )
        if coherence < 0.4:
            actions.append(
                f"Facilitate negotiation between commitments; coherence={coherence:.2f}"
            )
        if not actions:
            actions.append("Maintain course; resonance stable.")
        return actions

    def influence_graph(self, now: Optional[datetime] = None) -> Dict[str, List[Dict[str, str]]]:
        now = now or datetime.now(timezone.utc)
        aggregate = self._aggregate_signals(now)
        nodes = [
            {
                "id": f"commitment:{idx}",
                "label": c.intent,
                "actor": c.actor,
                "type": "commitment",
            }
            for idx, c in enumerate(self.commitments)
        ]
        signal_nodes = [
            {"id": f"signal:{k}", "label": k, "type": "signal", "value": v}
            for k, v in aggregate.items()
        ]
        edges = []
        for idx, commitment in enumerate(self.commitments):
            for feature in commitment.predicted_features:
                if feature in aggregate:
                    edges.append(
                        {
                            "source": f"commitment:{idx}",
                            "target": f"signal:{feature}",
                            "weight": commitment.predicted_features[feature],
                        }
                    )
        return {"nodes": nodes + signal_nodes, "edges": edges}

    def ingest_system_state(
        self,
        *,
        source: str,
        metrics: Dict[str, float],
        timestamp: Optional[datetime] = None,
        confidence: float = 1.0,
    ) -> SignalEvent:
        event = SignalEvent(
            source=source,
            timestamp=timestamp or datetime.now(timezone.utc),
            features=metrics,
            confidence=confidence,
        )
        self.ingest_event(event)
        return event


def demo_engine() -> List[ResonanceResult]:
    """Demonstration harness for notebooks or CLI experiments."""

    engine = ReciprocalResonanceEngine(decay_half_life_seconds=600)
    now = datetime.now(timezone.utc)
    engine.ingest_event(
        SignalEvent(
            source="observability",
            timestamp=now,
            features={"latency_ms": 120.0, "error_rate": 0.02},
            confidence=0.9,
        )
    )
    engine.ingest_event(
        SignalEvent(
            source="user-feedback",
            timestamp=now,
            features={"satisfaction": 0.76},
            confidence=0.7,
        )
    )

    engine.register_commitment(
        Commitment(
            actor="SRE",
            intent="Reduce latency by 20% without raising errors",
            predicted_features={"latency_ms": 95.0, "error_rate": 0.02},
            horizon_seconds=1800,
            risk_tolerance=0.4,
            weight=1.2,
        )
    )
    engine.register_commitment(
        Commitment(
            actor="Product",
            intent="Improve satisfaction to 0.85 via UX fixes",
            predicted_features={"satisfaction": 0.85},
            horizon_seconds=3600,
            risk_tolerance=0.6,
            weight=1.0,
        )
    )

    return engine.evaluate(now=now)


__all__ = [
    "SignalEvent",
    "Commitment",
    "ResonanceResult",
    "ReciprocalResonanceEngine",
    "demo_engine",
]
