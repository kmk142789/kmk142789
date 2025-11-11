"""Timebase helpers for the Atlas kernel."""

from __future__ import annotations

import statistics
import threading
import time
from collections import deque
from typing import Callable, Deque


class Timebase:
    """Maintains a controllable notion of time for the kernel."""

    def __init__(self, clock: Callable[[], float] | None = None, *, window: int = 128) -> None:
        self._clock = clock or time.monotonic
        self._start = self._clock()
        self._offset = 0.0
        self._ticks: Deque[float] = deque(maxlen=window)
        self._lock = threading.RLock()

    def now(self) -> float:
        with self._lock:
            return self._clock() + self._offset

    def adjust(self, offset: float) -> None:
        with self._lock:
            self._offset += offset

    def tick(self) -> float:
        with self._lock:
            current = self.now()
            self._ticks.append(current)
            return current

    def drift(self) -> float:
        with self._lock:
            if len(self._ticks) < 2:
                return 0.0
            ticks = list(self._ticks)
            intervals = [b - a for a, b in zip(ticks, ticks[1:])]
            return statistics.fmean(intervals) if intervals else 0.0

    def uptime(self) -> float:
        return self.now() - self._start


__all__ = ["Timebase"]
