"""Fusion kernel that synthesises meta-cognitive signals into one snapshot."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class FusionSnapshot:
    ranked_signals: List[Tuple[str, float]]
    conflicts: List[str]
    action_tendency: str
    confidence_profile: Dict[str, float]
    fused_payload: Dict[str, object]

    def to_dict(self) -> Dict[str, object]:
        return {
            "ranked_signals": [
                [label, float(score)] for label, score in self.ranked_signals
            ],
            "conflicts": list(self.conflicts),
            "action_tendency": self.action_tendency,
            "confidence_profile": dict(self.confidence_profile),
            "fused_payload": self.fused_payload,
        }


class CognitiveFusionKernel:
    """Combine predictions, emotions, bias and resonance into a single view."""

    def fuse(
        self,
        *,
        meta_report: Dict[str, object],
        prediction: Dict[str, object],
        resonance_triage: Dict[str, object],
        long_cycle_memory: List[Dict[str, object]],
    ) -> FusionSnapshot:
        emotional_inference = meta_report.get("emotional_inference", {})
        bias_correction = meta_report.get("bias_correction", {})
        self_debugging = meta_report.get("self_debugging", {})

        severity = resonance_triage.get("severity", "stable")
        sentiment_score = float(emotional_inference.get("sentiment_score", 0.0))
        optimism_bias = float(bias_correction.get("optimism_bias", 0.0))
        volatility_bias = float(bias_correction.get("volatility_bias", 0.0))
        prediction_confidence = 1.0 - min(1.0, optimism_bias + volatility_bias)

        ranked_signals = [
            ("resonance_severity", 1.0 if severity == "critical" else 0.75),
            ("sentiment", sentiment_score),
            ("prediction_confidence", prediction_confidence),
            ("bias_headroom", max(0.0, 1.0 - optimism_bias - volatility_bias)),
        ]
        ranked_signals = sorted(ranked_signals, key=lambda pair: pair[1], reverse=True)

        conflicts: List[str] = []
        if severity == "critical" and prediction.get("stability_outlook") == "resilient":
            conflicts.append("prediction_resonance_conflict")
        if optimism_bias > 0.08 and prediction_confidence > 0.9:
            conflicts.append("overconfident_prediction_with_bias")

        if severity == "critical":
            action_tendency = "stabilize"
        elif sentiment_score >= 0.8:
            action_tendency = "expand"
        else:
            action_tendency = "monitor"

        confidence_profile = {
            "sentiment": round(sentiment_score, 3),
            "prediction": round(prediction_confidence, 3),
            "memory_depth": float(len(long_cycle_memory)),
        }

        fused_payload = {
            "prediction": prediction,
            "emotional_inference": emotional_inference,
            "bias_correction": bias_correction,
            "resonance_triage": resonance_triage,
            "long_cycle_memory": long_cycle_memory,
            "self_debugging": self_debugging,
        }

        return FusionSnapshot(
            ranked_signals=ranked_signals,
            conflicts=conflicts,
            action_tendency=action_tendency,
            confidence_profile=confidence_profile,
            fused_payload=fused_payload,
        )
