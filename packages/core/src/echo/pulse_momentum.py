"""Cadence-aware momentum forecasting for the Echo pulse ledger.

The momentum model treats pulse events as a living heartbeat: it measures how
regularly the ledger is updated, spots bursts or droughts, and projects when
the next update should land.  The heuristics are intentionally deterministic
and dependency-free so they can run in automation pipelines or constrained
agents without needing extra packages.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean, median, pstdev
from typing import Iterable, List, Optional

from .echo_codox_kernel import PulseEvent


@dataclass(frozen=True)
class PulseMomentumForecast:
    """Forward-looking cadence snapshot for the pulse ledger."""

    sample_size: int
    cadence_label: str
    stability: float
    burstiness: float
    expected_next_timestamp: Optional[float]
    expected_next_iso: Optional[str]
    time_to_next_seconds: Optional[float]
    horizon_coverage: Optional[float]
    confidence: float
    mean_interval_seconds: Optional[float]
    median_interval_seconds: Optional[float]
    time_since_last_seconds: Optional[float]
    drought_alert: bool
    rationale: str
    now: float

    def to_dict(self) -> dict:
        return {
            "sample_size": self.sample_size,
            "cadence_label": self.cadence_label,
            "stability": self.stability,
            "burstiness": self.burstiness,
            "expected_next_timestamp": self.expected_next_timestamp,
            "expected_next_iso": self.expected_next_iso,
            "time_to_next_seconds": self.time_to_next_seconds,
            "horizon_coverage": self.horizon_coverage,
            "confidence": self.confidence,
            "mean_interval_seconds": self.mean_interval_seconds,
            "median_interval_seconds": self.median_interval_seconds,
            "time_since_last_seconds": self.time_since_last_seconds,
            "drought_alert": self.drought_alert,
            "rationale": self.rationale,
            "now": self.now,
        }


def compute_pulse_momentum(
    events: Iterable[PulseEvent],
    *,
    now: Optional[float] = None,
    horizon_hours: float = 36.0,
    lookback: int = 50,
) -> PulseMomentumForecast:
    """Return a cadence forecast derived from recent pulse events."""

    event_list: List[PulseEvent] = list(events)
    current_time = now if now is not None else datetime.now(tz=timezone.utc).timestamp()
    horizon_seconds = max(horizon_hours, 0.0) * 3600.0

    if len(event_list) < 2:
        rationale = "Need at least two events to establish cadence"
        time_since_last = None
        if event_list:
            time_since_last = max(0.0, current_time - event_list[-1].timestamp)
        return PulseMomentumForecast(
            sample_size=0,
            cadence_label="insufficient",
            stability=0.0,
            burstiness=0.0,
            expected_next_timestamp=None,
            expected_next_iso=None,
            time_to_next_seconds=None,
            horizon_coverage=None,
            confidence=0.0,
            mean_interval_seconds=None,
            median_interval_seconds=None,
            time_since_last_seconds=time_since_last,
            drought_alert=False,
            rationale=rationale,
            now=current_time,
        )

    trimmed_events = event_list[-(max(2, lookback) + 1) :]
    intervals: List[float] = [
        max(0.0, trimmed_events[index].timestamp - trimmed_events[index - 1].timestamp)
        for index in range(1, len(trimmed_events))
    ]
    sample_size = len(intervals)

    mean_interval = mean(intervals)
    median_interval = median(intervals)

    variation = 0.0
    if mean_interval > 0 and sample_size > 1:
        variation = pstdev(intervals) / mean_interval
    stability = max(0.0, min(1.0, 1.0 / (1.0 + variation)))

    burstiness = 0.0
    burst_threshold = 0.0
    if median_interval and mean_interval:
        burst_threshold = max(median_interval * 0.9, mean_interval * 0.6)
    if burst_threshold > 0:
        burstiness = sum(1 for value in intervals if value <= burst_threshold) / sample_size

    last_ts = trimmed_events[-1].timestamp
    time_since_last = max(0.0, current_time - last_ts)
    expected_next_timestamp = last_ts + median_interval
    time_to_next = expected_next_timestamp - current_time

    horizon_coverage = None
    if median_interval > 0:
        horizon_coverage = round(horizon_seconds / median_interval, 2) if horizon_seconds else 0.0

    confidence = min(1.0, max(0.05, stability * (sample_size / 5)))

    cadence_label = "steady"
    if time_since_last > max(median_interval * 1.8, horizon_seconds * 0.05):
        cadence_label = "dormant"
    elif stability < 0.35:
        cadence_label = "chaotic"
    elif burstiness >= 0.35:
        cadence_label = "bursty"
    elif time_since_last < median_interval * 0.6:
        cadence_label = "accelerating"

    drought_alert = time_since_last > median_interval * 2.0

    rationale = (
        f"sample={sample_size} cadence={cadence_label} stability={stability:.2f} "
        f"burstiness={burstiness:.2f} horizon={horizon_hours}h"
    )

    return PulseMomentumForecast(
        sample_size=sample_size,
        cadence_label=cadence_label,
        stability=stability,
        burstiness=burstiness,
        expected_next_timestamp=expected_next_timestamp,
        expected_next_iso=_format_timestamp(expected_next_timestamp),
        time_to_next_seconds=time_to_next,
        horizon_coverage=horizon_coverage,
        confidence=confidence,
        mean_interval_seconds=mean_interval,
        median_interval_seconds=median_interval,
        time_since_last_seconds=time_since_last,
        drought_alert=drought_alert,
        rationale=rationale,
        now=current_time,
    )


def _format_timestamp(timestamp: Optional[float]) -> Optional[str]:
    if timestamp is None:
        return None
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")
