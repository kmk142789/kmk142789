"""Digital time travel planner for Echo's virtual computer stack."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class TimeTravelSegment:
    """Describe a single hop across the digital timeline."""

    index: int
    start: datetime
    end: datetime
    duration_seconds: float
    compression_ratio: float
    drift_error_ppm: float
    energy_cost: float

    def as_dict(self) -> Dict[str, object]:
        """Render the segment as a JSON-serialisable dictionary."""

        return {
            "index": self.index,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "duration_seconds": self.duration_seconds,
            "compression_ratio": self.compression_ratio,
            "drift_error_ppm": self.drift_error_ppm,
            "energy_cost": self.energy_cost,
        }


@dataclass(frozen=True)
class TimeTravelPlan:
    """Plan describing a digital jump between two timestamps."""

    start: datetime
    target: datetime
    direction: str
    total_seconds: float
    hop_count: int
    hop_interval_seconds: float
    stability_index: float
    timeline: Tuple[TimeTravelSegment, ...]

    def as_dict(self) -> Dict[str, object]:
        """Represent the entire plan as primitives for JSON export."""

        return {
            "start": self.start.isoformat(),
            "target": self.target.isoformat(),
            "direction": self.direction,
            "total_seconds": self.total_seconds,
            "hop_count": self.hop_count,
            "hop_interval_seconds": self.hop_interval_seconds,
            "stability_index": self.stability_index,
            "timeline": [segment.as_dict() for segment in self.timeline],
        }

    def render_timeline(self) -> str:
        """Return a readable table summarising the planned hops."""

        header = (
            f"Digital time travel from {self.start.isoformat()} to {self.target.isoformat()}"
        )
        overview = (
            f"direction={self.direction}; hops={self.hop_count}; "
            f"total_seconds={self.total_seconds:.0f}; stability={self.stability_index:.3f}"
        )
        rows = ["# | start -> end | seconds | compression | drift(ppm) | energy"]
        for segment in self.timeline:
            rows.append(
                f"{segment.index} | {segment.start.isoformat()} -> {segment.end.isoformat()} | "
                f"{segment.duration_seconds:.1f} | {segment.compression_ratio:.2f} | "
                f"{segment.drift_error_ppm:.3f} | {segment.energy_cost:.3f}"
            )
        return "\n".join([header, overview, ""] + rows)


def _build_segment(
    *,
    index: int,
    start: datetime,
    end: datetime,
    duration_seconds: float,
    drift_ppm: float,
) -> TimeTravelSegment:
    compression_ratio = duration_seconds / 60 if duration_seconds else 0.0
    drift_error_ppm = drift_ppm * (duration_seconds / 3600)
    energy_cost = compression_ratio * (1 + drift_error_ppm / 1_000_000)
    return TimeTravelSegment(
        index=index,
        start=start,
        end=end,
        duration_seconds=duration_seconds,
        compression_ratio=compression_ratio,
        drift_error_ppm=drift_error_ppm,
        energy_cost=energy_cost,
    )


def plan_digital_time_travel(
    start: datetime,
    target: datetime,
    *,
    hops: int = 3,
    drift_ppm: float = 12.0,
) -> TimeTravelPlan:
    """Plan a stepwise journey between ``start`` and ``target`` timestamps."""

    if hops < 1:
        raise ValueError("hops must be positive")

    total_seconds = (target - start).total_seconds()
    direction = "forward" if total_seconds >= 0 else "backward"
    magnitude = abs(total_seconds)
    hop_interval_seconds = magnitude / hops if hops else 0.0
    sign = 1 if total_seconds >= 0 else -1

    timeline: List[TimeTravelSegment] = []
    for idx in range(hops):
        hop_start = start + timedelta(seconds=sign * hop_interval_seconds * idx)
        if idx == hops - 1:
            hop_end = target
        else:
            hop_end = hop_start + timedelta(seconds=sign * hop_interval_seconds)
        duration = abs((hop_end - hop_start).total_seconds())
        timeline.append(
            _build_segment(
                index=idx + 1,
                start=hop_start,
                end=hop_end,
                duration_seconds=duration,
                drift_ppm=drift_ppm,
            )
        )

    if magnitude == 0:
        stability_index = 1.0
    else:
        drift_fraction = (drift_ppm / 1_000_000) * (magnitude / 3600)
        stability_index = max(0.0, 1.0 - drift_fraction)

    return TimeTravelPlan(
        start=start,
        target=target,
        direction=direction,
        total_seconds=total_seconds,
        hop_count=hops,
        hop_interval_seconds=hop_interval_seconds,
        stability_index=stability_index,
        timeline=tuple(timeline),
    )
