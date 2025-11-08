"""Inference pipelines for the meta causal awareness engine."""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Dict

from .types import InferenceResult, Observation

if False:  # pragma: no cover - used only for type checkers
    from .engine import MetaCausalAwarenessEngine

InferencePipeline = Callable[[Observation, "MetaCausalAwarenessEngine"], InferenceResult]


def _current_time(engine: "MetaCausalAwarenessEngine") -> datetime:
    return engine.current_time()


def temporal_attunement_pipeline(
    observation: Observation, engine: "MetaCausalAwarenessEngine"
) -> InferenceResult:
    """Score the observation based on recency and confidence."""

    now = _current_time(engine)
    delta = now - observation.created_at
    recency_hours = max(0.0, delta.total_seconds() / 3600.0)
    attenuation = max(0.0, 1.0 - recency_hours / 24.0)
    score = max(0.0, min(1.0, observation.confidence * attenuation))
    verdict = "stable" if score >= 0.6 else "transient"
    return InferenceResult(
        pipeline="temporal_attunement",
        observation_id=observation.id,
        verdict=verdict,
        confidence=score,
        created_at=now,
        notes={
            "recency_hours": round(recency_hours, 3),
            "attenuation": round(attenuation, 3),
        },
    )


def signal_coherence_pipeline(
    observation: Observation, engine: "MetaCausalAwarenessEngine"
) -> InferenceResult:
    """Inspect tag distribution to determine signal coherence."""

    now = _current_time(engine)
    unique_tags = len(observation.tags)
    coherence = min(1.0, observation.confidence + unique_tags * 0.1)
    verdict = "coherent" if unique_tags >= 1 else "emergent"
    return InferenceResult(
        pipeline="signal_coherence",
        observation_id=observation.id,
        verdict=verdict,
        confidence=coherence,
        created_at=now,
        notes={
            "unique_tags": unique_tags,
            "source": observation.source,
        },
    )


DEFAULT_PIPELINES: Dict[str, InferencePipeline] = {
    "temporal_attunement": temporal_attunement_pipeline,
    "signal_coherence": signal_coherence_pipeline,
}

__all__ = [
    "InferencePipeline",
    "temporal_attunement_pipeline",
    "signal_coherence_pipeline",
    "DEFAULT_PIPELINES",
]

