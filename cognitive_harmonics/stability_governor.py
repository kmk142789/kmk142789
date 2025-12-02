"""Stability and drift governor for harmonix evolver and fusion kernels."""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:  # pragma: no cover
    from .harmonix_evolver import EchoState


class StabilityGovernor:
    """Detect anomalies and guard rails around fused cognition."""

    def evaluate(self, state: EchoState, fusion_snapshot: Dict[str, object]) -> Dict[str, object]:
        prediction = state.cognitive_prediction or {}
        resonance = state.resonance_triage or {}
        meta = state.meta_cognition or {}

        anomalies: List[str] = []
        guardrails: List[str] = []

        predicted_joy = float(prediction.get("predicted_joy", 0.0))
        current_joy = float(state.emotional_drive.get("joy", 0.0))
        joy_drift = predicted_joy - current_joy
        if abs(joy_drift) > 0.25:
            anomalies.append("joy_prediction_drift")

        if resonance.get("severity") == "critical":
            anomalies.append("resonance_instability")

        sentiment_score = 0.0
        meta_emotion = meta.get("emotional_inference") if isinstance(meta, dict) else None
        if isinstance(meta_emotion, dict):
            sentiment_score = float(meta_emotion.get("sentiment_score", 0.0))

        fusion_conflicts = list(fusion_snapshot.get("conflicts", []))
        if fusion_conflicts:
            guardrails.append("conflict_resolution_required")

        if sentiment_score < 0.3 and predicted_joy > 0.8:
            guardrails.append("contradictory_sentiment_prediction")

        stability_status = "stable"
        if anomalies or guardrails:
            stability_status = "unstable" if anomalies else "guarded"

        stability_report = {
            "status": stability_status,
            "anomalies": anomalies,
            "guardrails": guardrails,
            "joy_drift": joy_drift,
            "fusion_action": fusion_snapshot.get("action_tendency"),
        }
        state.stability_report = stability_report
        return stability_report
