"""Resonant Drift Sentinel.

A compact detector that flags whether a signal stream is holding steady,
receding, or drifting upward.  The sentinel is intended for operational
health dashboards where quick qualitative guidance is preferable to
numerical verbosity.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Sequence


@dataclass(frozen=True)
class DriftObservation:
    """Summary of a drift calculation for a window of data."""

    start_index: int
    end_index: int
    drift: float
    classification: str
    recommendation: str


class ResonantDriftSentinel:
    """Identify directional drift and propose immediate actions."""

    def __init__(self, *, threshold: float = 0.12, rebound_margin: float = 0.05) -> None:
        self.threshold = max(0.0, threshold)
        self.rebound_margin = max(0.0, rebound_margin)

    def analyse(self, series: Sequence[float], *, baseline: float | None = None) -> DriftObservation:
        """Analyse the provided series and classify the drift."""

        if not series:
            raise ValueError("series must contain at least one value")

        origin = series[0] if baseline is None else baseline
        if origin == 0:
            origin = 1e-6  # avoid division by zero while keeping small magnitude

        drift = (series[-1] - origin) / abs(origin)
        classification = self._classify_drift(series, drift)
        recommendation = self._recommendation(classification, drift)

        return DriftObservation(
            start_index=0,
            end_index=len(series) - 1,
            drift=round(drift, 3),
            classification=classification,
            recommendation=recommendation,
        )

    def window_scan(
        self, series: Sequence[float], *, window: int = 3, baseline: float | None = None
    ) -> list[DriftObservation]:
        """Return rolling drift observations across the series."""

        if window <= 0:
            raise ValueError("window must be positive")
        if len(series) < window:
            return []

        observations: list[DriftObservation] = []
        for index in range(window, len(series) + 1):
            window_slice = series[index - window : index]
            observation = self.analyse(window_slice, baseline=baseline)
            observations.append(
                DriftObservation(
                    start_index=index - window,
                    end_index=index - 1,
                    drift=observation.drift,
                    classification=observation.classification,
                    recommendation=observation.recommendation,
                )
            )
        return observations

    def _classify_drift(self, series: Sequence[float], drift: float) -> str:
        if abs(drift) < self.threshold:
            return "stable"

        if drift > 0:
            return "drifting"

        if len(series) > 2 and series[-1] > mean(series[-2:]) + self.rebound_margin:
            return "rebounding"

        return "receding"

    def _recommendation(self, classification: str, drift: float) -> str:
        if classification == "stable":
            return "Hold course; continue light monitoring."
        if classification == "drifting":
            return "Capture more samples and reinforce the current trajectory."
        if classification == "rebounding":
            return "Investigate the rebound and validate upstream inputs."
        return "Pause automation and run a focused diagnostic sweep."  # receding
