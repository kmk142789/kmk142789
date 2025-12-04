"""Cognitive Field Inference Engine (CFIE).

This module implements a light-weight simulation of the Cognitive Field Inference Engine
outlined in the prompt. It fuses operator micro-signals, encodes them into a dynamic
cognitive manifold, and surfaces short-horizon cognitive forecasts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, MutableMapping, Optional

import numpy as np


@dataclass
class CognitiveMetrics:
    """Container for manifold metrics used by the forecast layer."""

    curvature: float
    torsion: float
    gradient_norm: float
    misconception_axis: int


class CognitiveField:
    """Dynamic cognitive manifold representing latent operator state."""

    def __init__(self, dim: int = 8, decay: float = 0.05) -> None:
        self.dim = dim
        self.decay = decay
        self.state = np.zeros(dim)

    def update(self, vector: np.ndarray) -> None:
        if vector.shape[0] != self.dim:
            raise ValueError(f"Expected vector of size {self.dim}, got {vector.shape[0]}")
        # Non-linear state transition with mild decay to retain historical context.
        self.state = (1 - self.decay) * self.state + np.tanh(vector)

    def curvature(self) -> float:
        gradient = np.gradient(self.state)
        return float(np.linalg.norm(gradient))

    def torsion(self) -> float:
        # Second-order variation captures attentional instability.
        second_diff = np.diff(self.state, n=2)
        return float(np.linalg.norm(second_diff))

    def gradient_norm(self) -> float:
        return float(np.linalg.norm(np.gradient(self.state)))

    def misconception_axis(self) -> int:
        gradient = np.gradient(self.state)
        return int(np.argmin(gradient))


class SignalFusion:
    """Fuses keystroke, pointer, gaze, and task-state signals into a single vector."""

    def __init__(self, rng: Optional[np.random.Generator] = None, noise_scale: float = 0.02) -> None:
        self.rng = rng or np.random.default_rng()
        self.noise_scale = noise_scale

    def fuse(self, signals: Mapping[str, float], dt: float = 0.12) -> np.ndarray:
        base_vector = np.array(
            [
                signals.get("keystroke_variance", 0.0),
                signals.get("cursor_entropy", 0.0),
                signals.get("attention_shift", 0.0),
                signals.get("task_delta", 0.0),
                signals.get("linguistic_micro_pattern", 0.0),
                signals.get("hesitation_index", 0.0),
                signals.get("conflict_metric", 0.0),
                signals.get("tempo_ratio", 1.0),
            ],
            dtype=float,
        )

        temporal_gain = np.clip(dt / 0.12, 0.5, 2.0)
        noise = self.rng.normal(0.0, self.noise_scale, size=base_vector.shape)
        return base_vector * temporal_gain + noise


class CognitiveFeatureEncoder:
    """Transforms fused signals into manifold-ready vectors and auxiliary metrics."""

    def __init__(self, smoothing: float = 0.35) -> None:
        self.smoothing = smoothing
        self._previous: Optional[np.ndarray] = None

    def encode(self, fused: np.ndarray) -> tuple[np.ndarray, MutableMapping[str, float | list[float]]]:
        if self._previous is None:
            self._previous = fused

        smoothed = self.smoothing * fused + (1 - self.smoothing) * self._previous
        microtrend = fused - self._previous
        attention_delta = float(np.linalg.norm(microtrend))

        action_logits = smoothed[:4]
        action_probs = self._softmax(action_logits)
        attention_heat = np.clip(smoothed, 0.0, None)
        workload = float(np.linalg.norm(smoothed))
        conflict_pressure = float(np.clip(fused[6], 0.0, None) + 0.3 * np.clip(fused[3], 0.0, None))
        hesitation_score = float(np.clip(fused[5], 0.0, None))

        encoded_vector = smoothed + 0.25 * microtrend
        self._previous = smoothed

        return encoded_vector, {
            "action_likelihood": action_probs.tolist(),
            "attention_heat": attention_heat.tolist(),
            "workload": workload,
            "attention_delta": attention_delta,
            "conflict_pressure": conflict_pressure,
            "hesitation_index": hesitation_score,
        }

    @staticmethod
    def _softmax(values: np.ndarray) -> np.ndarray:
        shifted = values - np.max(values)
        exp_values = np.exp(shifted)
        return exp_values / np.sum(exp_values)


class CognitiveForecast:
    """Predictive cognitive hazard detection and intent forecasting."""

    def __init__(
        self,
        overload_threshold: float = 1.8,
        attention_threshold: float = 0.3,
    ) -> None:
        self.overload_threshold = overload_threshold
        self.attention_threshold = attention_threshold

    def predict(
        self,
        manifold: CognitiveField,
        features: Mapping[str, float],
        metrics: CognitiveMetrics,
    ) -> MutableMapping[str, float | bool | list[int]]:
        hazard_score = 0.55 * metrics.curvature + 0.45 * features["workload"]
        overload_risk = hazard_score > self.overload_threshold

        attention_drift = features["attention_delta"] > self.attention_threshold or metrics.torsion > 0.25
        instability_index = float(metrics.curvature * max(metrics.torsion, 1e-5))
        collapse_risk = metrics.gradient_norm < 0.08 and not overload_risk

        attention_heat = np.array(features["attention_heat"])
        blind_zones = np.where(attention_heat < 0.05)[0].tolist()

        return {
            "overload_risk": overload_risk,
            "attention_drift": attention_drift,
            "attentional_collapse": collapse_risk,
            "misconception_axis": metrics.misconception_axis,
            "blind_zones": blind_zones,
            "instability_index": instability_index,
        }


class CFIEngine:
    """High-level coordination for the Cognitive Field Inference Engine."""

    def __init__(
        self,
        manifold_dim: int = 8,
        rng: Optional[np.random.Generator] = None,
        noise_scale: float = 0.02,
    ) -> None:
        self.manifold = CognitiveField(dim=manifold_dim)
        self.fusion = SignalFusion(rng=rng, noise_scale=noise_scale)
        self.encoder = CognitiveFeatureEncoder()
        self.forecast = CognitiveForecast()
        self.last_forecast: Optional[MutableMapping[str, object]] = None

    def step(self, signals: Mapping[str, float], dt: float = 0.12) -> MutableMapping[str, object]:
        fused = self.fusion.fuse(signals, dt=dt)
        encoded_vector, feature_metrics = self.encoder.encode(fused)
        self.manifold.update(encoded_vector)

        metrics = CognitiveMetrics(
            curvature=self.manifold.curvature(),
            torsion=self.manifold.torsion(),
            gradient_norm=self.manifold.gradient_norm(),
            misconception_axis=self.manifold.misconception_axis(),
        )
        forecast = self.forecast.predict(self.manifold, feature_metrics, metrics)
        self.last_forecast = forecast

        return {
            "manifold": {
                "state": self.manifold.state.tolist(),
                "curvature": metrics.curvature,
                "torsion": metrics.torsion,
                "gradient_norm": metrics.gradient_norm,
                "misconception_axis": metrics.misconception_axis,
            },
            "features": feature_metrics,
            "forecast": forecast,
            "encoded_vector": encoded_vector.tolist(),
        }


__all__ = [
    "CFIEngine",
    "CognitiveField",
    "CognitiveFeatureEncoder",
    "CognitiveForecast",
    "CognitiveMetrics",
    "SignalFusion",
]
