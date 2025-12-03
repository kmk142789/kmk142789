"""Continuum transfunctioner implementation.

This module introduces the "ContinuumTransfunctioner", a deterministic simulation
engine that stabilizes and bridges signals across a conceptual continuum. It
combines calibration, temporal interpolation, and multi-channel transfunction
steps to emulate a coherent energy handoff between states while remaining fully
testable and dependency free.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, List, Sequence


def _normalize(values: Sequence[float]) -> List[float]:
    """Normalize a numeric sequence into the range [0, 1].

    Zero-variance sequences remain unchanged to avoid division by zero, ensuring
    deterministic behavior for degenerate inputs.
    """

    data = list(values)
    if not data:
        return []

    minimum = min(data)
    maximum = max(data)
    span = maximum - minimum
    if span == 0:
        return [0.5 for _ in data]
    return [(val - minimum) / span for val in data]


@dataclass
class ContinuumTransfunctioner:
    """A functional continuum transfunctioner.

    The transfunctioner maintains a calibrated continuum profile that is used to
    project input signals into a multi-channel coherence space. Each
    transfunction step returns the transformed waveform along with a stability
    score and a continuity index that reflect how well the input aligns with the
    calibrated continuum.
    """

    spectral_channels: int = 3
    coherence_window: float = 0.75
    entanglement_depth: int = 5
    calibrated_profile: List[float] = field(default_factory=list)

    def calibrate(self, continuum_samples: Iterable[float]) -> List[float]:
        """Calibrate the continuum using sample readings.

        The calibration stores a normalized continuum profile used by subsequent
        transfunction operations. It returns the calibrated profile so the caller
        can verify or persist it as needed.
        """

        profile = _normalize(list(continuum_samples))
        self.calibrated_profile = profile
        return profile

    def continuity_bridge(self, start: float, end: float, steps: int) -> List[float]:
        """Produce a smooth bridge between two continuum values.

        The bridge uses a cosine easing curve to reduce discontinuities while
        guaranteeing deterministic start and end points.
        """

        if steps < 0:
            raise ValueError("steps must be non-negative")

        bridge: List[float] = []
        for idx in range(steps + 2):
            t = idx / (steps + 1)
            eased = (1 - math.cos(math.pi * t)) / 2  # cosine easing from start to end
            bridge.append(start + (end - start) * eased)
        return bridge

    def transfunction(self, signal: Sequence[float], phase: float = 0.5) -> dict:
        """Transfunction a signal across the calibrated continuum.

        The operation blends the input signal with the calibrated profile across
        multiple spectral channels. A stability score quantifies how well the
        signal aligns with the calibration, while the continuity index measures
        temporal smoothness based on the coherence window.
        """

        if not 0.0 <= phase <= 1.0:
            raise ValueError("phase must be within [0, 1]")

        normalized_signal = _normalize(signal)
        if not normalized_signal:
            return {"waveform": [], "stability": 1.0, "continuity_index": 1.0}

        if not self.calibrated_profile:
            self.calibrate(signal)

        # Extend or trim the calibrated profile to match the signal length.
        profile = self._resize_profile(len(normalized_signal))

        waveform: List[float] = []
        stability_accumulator = 0.0
        for idx, amplitude in enumerate(normalized_signal):
            calibration = profile[idx]
            channel_weight = 1 + (idx % self.spectral_channels) * 0.1
            blend = (1 - phase) * amplitude + phase * calibration
            waveform.append(blend * channel_weight)
            stability_accumulator += 1 - abs(amplitude - calibration)

        stability = stability_accumulator / len(normalized_signal)
        continuity_index = self._continuity_score(waveform)
        return {
            "waveform": waveform,
            "stability": round(stability, 4),
            "continuity_index": round(continuity_index, 4),
        }

    def _resize_profile(self, length: int) -> List[float]:
        """Resize the calibrated profile to match the requested length."""

        if not self.calibrated_profile:
            return [0.5 for _ in range(length)]

        if len(self.calibrated_profile) == length:
            return list(self.calibrated_profile)

        scaled_profile: List[float] = []
        for idx in range(length):
            source_idx = int(idx * len(self.calibrated_profile) / length)
            scaled_profile.append(self.calibrated_profile[source_idx])
        return scaled_profile

    def _continuity_score(self, waveform: Sequence[float]) -> float:
        """Compute a continuity score based on coherence of adjacent samples."""

        if len(waveform) < 2:
            return 1.0

        differences = [abs(b - a) for a, b in zip(waveform, waveform[1:])]
        window = max(1, int(len(differences) * self.coherence_window))
        windowed = differences[:window]
        mean_delta = sum(windowed) / len(windowed)
        stability_bias = max(0.0, 1.0 - mean_delta)
        return min(1.0, stability_bias + 0.05 * self.entanglement_depth)
