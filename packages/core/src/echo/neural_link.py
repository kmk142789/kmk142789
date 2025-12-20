"""NeuralLink system for harmonizing neural oracles with OuterLink telemetry."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import fmean, pstdev
from typing import Any, Iterable, Mapping, Sequence, Tuple

from .neural_network_oracle import NeuralNetworkOracle, OraclePrediction

__all__ = [
    "NeuralLinkPulse",
    "NeuralLinkCalibration",
    "NeuralLinkSystem",
]


@dataclass(slots=True, frozen=True)
class NeuralLinkPulse:
    """Normalized neural signal compatible with OuterLink payloads."""

    features: Tuple[float, ...]
    prediction: OraclePrediction
    source: str
    outerlink_digest: str | None
    created_at: str

    def to_outerlink_payload(self) -> dict[str, object]:
        """Render the pulse as an OuterLink-compatible payload."""

        return {
            "created_at": self.created_at,
            "source": self.source,
            "outerlink_digest": self.outerlink_digest,
            "features": list(self.features),
            "signal": self.prediction.signal,
            "confidence": self.prediction.confidence,
            "vector": list(self.prediction.vector),
            "narrative": self.prediction.narrative,
        }


@dataclass(slots=True)
class NeuralLinkCalibration:
    """Lightweight calibration snapshot for neural link features."""

    feature_means: Tuple[float, ...]
    feature_scales: Tuple[float, ...]
    sample_count: int


class NeuralLinkSystem:
    """Upgrade-ready neural link that bridges predictions and OuterLink state."""

    def __init__(
        self,
        *,
        input_size: int = 6,
        hidden_layers: Sequence[int] = (8, 6),
        output_size: int = 1,
        seed: int | None = 0,
    ) -> None:
        self.oracle = NeuralNetworkOracle(
            input_size=input_size,
            hidden_layers=hidden_layers,
            output_size=output_size,
            seed=seed,
        )
        self._feature_samples: list[Tuple[float, ...]] = []
        self._history: list[NeuralLinkPulse] = []

    @staticmethod
    def _metric(payload: Mapping[str, Any], key: str, default: float = 0.0) -> float:
        value = payload.get(key, default)
        try:
            return float(value) if value is not None else float(default)
        except (TypeError, ValueError):
            return float(default)

    def _features_from_outerlink(self, state: Mapping[str, Any]) -> Tuple[float, ...]:
        metrics = state.get("metrics", {}) or {}
        offline = state.get("offline", {}) or {}
        events = state.get("events", {}) or {}

        online = 1.0 if state.get("online") else 0.0
        pending = self._metric(offline, "pending_events")
        cached = self._metric(offline, "cached_events")
        resilience = self._metric(offline, "resilience_score")
        storage_free = self._metric(metrics, "storage_free_mb") / 1024.0
        event_total = self._metric(events, "total")

        return (online, pending, cached, resilience, storage_free, event_total)

    def record_features(self, features: Sequence[float]) -> None:
        self._feature_samples.append(tuple(features))

    def recalibrate(self) -> NeuralLinkCalibration:
        if not self._feature_samples:
            calibration = NeuralLinkCalibration(feature_means=tuple(), feature_scales=tuple(), sample_count=0)
            return calibration

        columns = list(zip(*self._feature_samples))
        means = tuple(fmean(column) for column in columns)
        scales = tuple(max(pstdev(column), 1e-6) for column in columns)
        self.oracle._feature_means = list(means)
        self.oracle._feature_scales = list(scales)
        return NeuralLinkCalibration(
            feature_means=means,
            feature_scales=scales,
            sample_count=len(self._feature_samples),
        )

    def pulse_from_outerlink(self, state: Mapping[str, Any], *, source: str = "outerlink") -> NeuralLinkPulse:
        features = self._features_from_outerlink(state)
        self.record_features(features)
        prediction = self.oracle.predict(features)
        pulse = NeuralLinkPulse(
            features=features,
            prediction=prediction,
            source=source,
            outerlink_digest=state.get("digest"),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._history.append(pulse)
        return pulse

    def pulse_from_features(self, features: Sequence[float], *, source: str = "manual") -> NeuralLinkPulse:
        payload = tuple(features)
        self.record_features(payload)
        prediction = self.oracle.predict(payload)
        pulse = NeuralLinkPulse(
            features=payload,
            prediction=prediction,
            source=source,
            outerlink_digest=None,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._history.append(pulse)
        return pulse

    def history(self) -> Tuple[NeuralLinkPulse, ...]:
        return tuple(self._history)
