"""Lightweight metrics service for Atlas integrations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Dict, List
import json


@dataclass(slots=True)
class TimingStats:
    """Summary statistics for a recorded timing series."""

    samples: List[float] = field(default_factory=list)

    def add(self, value: float) -> None:
        self.samples.append(float(value))

    def as_dict(self) -> Dict[str, float | int]:
        if not self.samples:
            return {"count": 0, "min": 0.0, "max": 0.0, "avg": 0.0, "total": 0.0}
        return {
            "count": len(self.samples),
            "min": min(self.samples),
            "max": max(self.samples),
            "avg": mean(self.samples),
            "total": sum(self.samples),
        }


class AtlasMetricsService:
    """Collect counters and timings for Atlas oriented workflows."""

    def __init__(self) -> None:
        self._counters: Dict[str, int] = {}
        self._timings: Dict[str, TimingStats] = {}

    def increment(self, name: str, value: int = 1) -> None:
        """Increase *name* by *value* (defaults to 1)."""

        if value < 0:
            raise ValueError("counter increments must be non-negative")
        self._counters[name] = self._counters.get(name, 0) + int(value)

    def set(self, name: str, value: int) -> None:
        """Set *name* to a specific integer value."""

        self._counters[name] = int(value)

    def observe(self, name: str, value: float) -> None:
        """Record a timing sample for *name*."""

        stats = self._timings.setdefault(name, TimingStats())
        stats.add(value)

    def snapshot(self) -> Dict[str, object]:
        """Return the current metrics without mutating internal state."""

        return {
            "counters": dict(self._counters),
            "timings": {key: stats.as_dict() for key, stats in self._timings.items()},
        }

    def export(self, path: Path) -> None:
        """Write the metrics snapshot to *path* as JSON."""

        payload = self.snapshot()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def reset(self) -> None:
        """Clear all recorded metrics."""

        self._counters.clear()
        self._timings.clear()


__all__ = ["AtlasMetricsService", "TimingStats"]
