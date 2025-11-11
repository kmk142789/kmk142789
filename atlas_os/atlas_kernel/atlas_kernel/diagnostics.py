"""Diagnostic utilities for observing Atlas kernel behaviour."""

from __future__ import annotations

import statistics
import threading
import time
from collections import Counter, deque
from dataclasses import dataclass
from typing import Deque, Dict, Iterable, Optional


@dataclass(slots=True)
class KernelEvent:
    """Represents a single observable event in the kernel."""

    timestamp: float
    lane: str
    event: str
    duration: float | None = None


class KernelDiagnostics:
    """Tracks scheduling and timing information for the kernel."""

    def __init__(self, *, window: int = 512) -> None:
        self._events: Deque[KernelEvent] = deque(maxlen=window)
        self._lane_activity: Counter[str] = Counter()
        self._lock = threading.RLock()
        self._last_heartbeat = time.monotonic()
        self._total_runtime = 0.0

    def record_microtask(self, lane: str, duration: float) -> None:
        event = KernelEvent(time.monotonic(), lane, "microtask", duration)
        with self._lock:
            self._events.append(event)
            self._lane_activity[lane] += 1
            self._total_runtime += max(duration, 0.0)

    def record_timer(self, lane: str, waited: float) -> None:
        event = KernelEvent(time.monotonic(), lane, "timer", waited)
        with self._lock:
            self._events.append(event)
            self._lane_activity[lane] += 1
            self._total_runtime += max(waited, 0.0)

    def heartbeat(self) -> None:
        with self._lock:
            self._last_heartbeat = time.monotonic()

    def stalled_for(self) -> float:
        with self._lock:
            return max(0.0, time.monotonic() - self._last_heartbeat)

    def active_lanes(self) -> Iterable[str]:
        with self._lock:
            return list(self._lane_activity.keys())

    def lane_pressure(self, lane: str) -> int:
        with self._lock:
            return self._lane_activity.get(lane, 0)

    def summary(self) -> Dict[str, float | int]:
        with self._lock:
            durations = [event.duration or 0.0 for event in self._events]
            return {
                "events": len(self._events),
                "avg_duration": statistics.fmean(durations) if durations else 0.0,
                "max_duration": max(durations, default=0.0),
                "lanes": len(self._lane_activity),
                "total_runtime": self._total_runtime,
            }

    def recent_events(self, *, limit: Optional[int] = None) -> Iterable[KernelEvent]:
        with self._lock:
            if limit is None or limit >= len(self._events):
                return list(self._events)
            return list(self._events)[-limit:]


__all__ = ["KernelDiagnostics", "KernelEvent"]
