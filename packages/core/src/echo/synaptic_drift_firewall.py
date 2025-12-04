"""Synaptic Drift Firewall: counterfactual resilience mesh.

This module introduces a new capability that fuses cognitive predictive processing with
counterfactual inference to arrest cross-system drift. It builds a lightweight
"firewall" that reasons about signals, generates plausible alternative states, and
issues actionable alignment playbooks.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from pydantic import BaseModel, Field


class SignalEnvelope(BaseModel):
    """Canonical wrapper for incoming telemetry and intent signals."""

    source: str
    channel: str
    payload: Dict[str, object]
    timestamp: float
    importance: float = Field(default=1.0, ge=0.1, le=10.0)


@dataclass
class Counterfactual:
    """Represents a synthesized plausible state."""

    name: str
    vector: List[float]
    rationale: str


@dataclass
class DriftDecision:
    """Outcome of evaluating a signal against the firewall."""

    verdict: str
    score: float
    counterfactual: Counterfactual
    explanation: str
    playbook: Dict[str, object] = field(default_factory=dict)


class FeatureProjector:
    """Projects mixed payloads into numeric state vectors.

    The projector applies a deterministic mapping that combines:
    - direct numeric values
    - ordinal encodings for strings (length + vowel density + hash parity)
    - stabilizers that keep dimensionality consistent across events
    """

    def encode(self, payload: Dict[str, object]) -> List[float]:
        features: List[float] = []
        for key in sorted(payload.keys()):
            value = payload[key]
            if isinstance(value, (int, float)):
                features.append(float(value))
            elif isinstance(value, str):
                features.extend(self._encode_text(value))
            else:
                features.append(float(hash(str(value)) % 97) / 97.0)
        stabilizers = self._stabilize(len(features))
        return features + stabilizers

    def _encode_text(self, text: str) -> List[float]:
        length = len(text)
        vowels = sum(1 for c in text.lower() if c in "aeiou")
        parity = 1.0 if hash(text) % 2 == 0 else -1.0
        density = vowels / max(length, 1)
        return [float(length), density, parity]

    def _stabilize(self, feature_len: int) -> List[float]:
        """Adds small deterministic stabilizers to reach a minimum vector size."""

        target = max(6, feature_len)
        stabilizers = []
        for idx in range(feature_len, target):
            stabilizers.append(math.sin(idx + 1))
        return stabilizers


class CounterfactualEngine:
    """Synthesizes counterfactuals grounded in predictive processing."""

    def __init__(self, projector: FeatureProjector):
        self.projector = projector

    def generate(
        self, current: List[float], history: Sequence[List[float]]
    ) -> List[Counterfactual]:
        baseline = self._baseline(history)
        volatility = self._volatility(history, baseline)
        inverted = [b - (x - b) * 0.5 for x, b in zip(current, baseline)]
        dampened = [x - v for x, v in zip(current, volatility)]
        projected = self._project_forward(current, history)
        return [
            Counterfactual(
                name="phase_inversion",
                vector=inverted,
                rationale="Reflects the anomaly into the latent manifold to test alignment.",
            ),
            Counterfactual(
                name="volatility_cooling",
                vector=dampened,
                rationale="Cools the signal by recent volatility to probe stability thresholds.",
            ),
            Counterfactual(
                name="temporal_projection",
                vector=projected,
                rationale="Projects the trendline one step to detect anticipatory drift.",
            ),
        ]

    def _baseline(self, history: Sequence[List[float]]) -> List[float]:
        if not history:
            return []
        length = max(len(vec) for vec in history)
        padded = [self._pad(vec, length) for vec in history]
        return [statistics.fmean(values) for values in zip(*padded)]

    def _volatility(
        self, history: Sequence[List[float]], baseline: Sequence[float]
    ) -> List[float]:
        if not history:
            return []
        length = max(len(vec) for vec in history)
        padded = [self._pad(vec, length) for vec in history]
        variance = []
        for col, base in zip(zip(*padded), baseline):
            variance.append(statistics.fmean(abs(x - base) for x in col))
        return variance

    def _project_forward(
        self, current: List[float], history: Sequence[List[float]]
    ) -> List[float]:
        if len(history) < 2:
            return current
        last = self._pad(history[-1], len(current))
        prev = self._pad(history[-2], len(current))
        delta = [l - p for l, p in zip(last, prev)]
        return [c + d for c, d in zip(current, delta)]

    @staticmethod
    def _pad(vector: Sequence[float], target: int) -> List[float]:
        pad_size = target - len(vector)
        if pad_size <= 0:
            return list(vector)
        return list(vector) + [0.0] * pad_size


class SynapticDriftFirewall:
    """Main coordination point for the capability."""

    def __init__(
        self,
        window: int = 24,
        tolerance: float = 0.18,
        projector: Optional[FeatureProjector] = None,
    ) -> None:
        self.window = window
        self.tolerance = tolerance
        self.projector = projector or FeatureProjector()
        self.counterfactual_engine = CounterfactualEngine(self.projector)
        self.history: List[Tuple[SignalEnvelope, List[float]]] = []

    def observe(self, signal: SignalEnvelope) -> DriftDecision:
        vector = self.projector.encode(signal.payload)
        self.history.append((signal, vector))
        self.history = self.history[-self.window :]
        return self.evaluate(signal, vector)

    def evaluate(self, signal: SignalEnvelope, vector: List[float]) -> DriftDecision:
        facts = [vec for _, vec in self.history if vec is not vector]
        counterfactuals = self.counterfactual_engine.generate(vector, facts)
        baseline = self.counterfactual_engine._baseline(facts)
        best = min(
            counterfactuals,
            key=lambda cf: self._resonance_distance(cf.vector, vector, baseline, signal.importance),
        )
        score = self._resonance_distance(best.vector, vector, baseline, signal.importance)
        verdict = self._verdict(score, signal.importance)
        explanation = self._explain(verdict, score, best, signal)
        playbook = self._playbook(verdict, signal, best)
        return DriftDecision(
            verdict=verdict,
            score=score,
            counterfactual=best,
            explanation=explanation,
            playbook=playbook,
        )

    def _resonance_distance(
        self,
        counterfactual: List[float],
        observation: List[float],
        baseline: List[float],
        importance: float,
    ) -> float:
        length = max(len(counterfactual), len(observation), len(baseline))
        cf = CounterfactualEngine._pad(counterfactual, length)
        ob = CounterfactualEngine._pad(observation, length)
        base = CounterfactualEngine._pad(baseline, length)
        surprise = math.sqrt(sum((c - o) ** 2 for c, o in zip(cf, ob)))
        prior_pull = sum(abs(o - b) for o, b in zip(ob, base))
        coherence_terms = []
        for c, o in zip(cf, ob):
            denom = abs(o) + 1e-6
            coherence_terms.append(max(0.0, 1.0 - abs(c - o) / denom))
        coherence = sum(coherence_terms) / (length or 1)
        base_score = (surprise + 0.5 * prior_pull - 0.3 * coherence) / (length or 1)
        drift_floor = (prior_pull / (length or 1)) * 0.1
        weighted = (base_score + drift_floor) * (importance ** 0.5)
        return max(weighted, 0.0)

    def _verdict(self, score: float, importance: float) -> str:
        if score < self.tolerance * 0.5:
            return "aligned"
        if score < self.tolerance * (1.0 + importance * 0.05):
            return "watch"
        return "contain"

    def _explain(
        self, verdict: str, score: float, best: Counterfactual, signal: SignalEnvelope
    ) -> str:
        return (
            f"Verdict={verdict} with resonance score {score:.4f} using {best.name} because "
            f"source={signal.source} channel={signal.channel} diverged from prior manifold."
        )

    def _playbook(
        self, verdict: str, signal: SignalEnvelope, counterfactual: Counterfactual
    ) -> Dict[str, object]:
        if verdict == "aligned":
            return {
                "action": "mirror",
                "notes": "Signal aligned with priors; propagate to knowledge fabric.",
            }
        if verdict == "watch":
            return {
                "action": "shadow_sim",
                "counterfactual_probe": counterfactual.name,
                "notes": "Shadow-simulate downstream flows before committing changes.",
            }
        return {
            "action": "contain",
            "counterfactual_probe": counterfactual.name,
            "notes": "Isolate channel, request human-in-the-loop approval, and replay with probe.",
        }

    def export_alignment_patch(self, decision: DriftDecision) -> Dict[str, object]:
        """Creates a portable patch for integration surfaces (dashboards, pipelines)."""

        return {
            "verdict": decision.verdict,
            "score": decision.score,
            "counterfactual": decision.counterfactual.name,
            "playbook": decision.playbook,
            "explanation": decision.explanation,
        }

    def alignment_mesh_snapshot(self) -> Dict[str, object]:
        """Summarizes the current state for external observers."""

        recent_sources = {envelope.source for envelope, _ in self.history}
        recent_channels = {envelope.channel for envelope, _ in self.history}
        return {
            "window": self.window,
            "observations": len(self.history),
            "sources": sorted(recent_sources),
            "channels": sorted(recent_channels),
        }


def run_demo() -> None:
    firewall = SynapticDriftFirewall(window=6, tolerance=0.2)
    seeds = [
        SignalEnvelope(
            source="telemetry",
            channel="edge-A",
            payload={"latency": 120, "loss": 0.02},
            timestamp=1.0,
        ),
        SignalEnvelope(
            source="telemetry",
            channel="edge-A",
            payload={"latency": 125, "loss": 0.03},
            timestamp=2.0,
        ),
        SignalEnvelope(
            source="intent",
            channel="policy",
            payload={"mode": "safe", "budget": 0.8},
            timestamp=3.0,
        ),
    ]
    for seed in seeds:
        firewall.observe(seed)

    probe = SignalEnvelope(
        source="telemetry",
        channel="edge-A",
        payload={"latency": 190, "loss": 0.07, "mode": "overdrive"},
        timestamp=4.0,
        importance=1.6,
    )
    decision = firewall.observe(probe)
    patch = firewall.export_alignment_patch(decision)
    print(decision.explanation)
    print(patch)


if __name__ == "__main__":
    run_demo()
