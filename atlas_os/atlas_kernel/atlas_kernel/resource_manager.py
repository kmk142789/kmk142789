"""Resource management primitives for the Atlas kernel."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Dict

_LOGGER = logging.getLogger(__name__)


@dataclass
class ResourceBudget:
    cpu_seconds: float
    memory_bytes: int
    lane: str = "default"
    usage_seconds: float = 0.0
    usage_bytes: int = 0

    def consume_cpu(self, seconds: float) -> None:
        self.usage_seconds += seconds
        if self.usage_seconds > self.cpu_seconds:
            raise RuntimeError(f"CPU budget exceeded for lane {self.lane}")

    def consume_memory(self, bytes_count: int) -> None:
        self.usage_bytes += bytes_count
        if self.usage_bytes > self.memory_bytes:
            raise RuntimeError(f"Memory budget exceeded for lane {self.lane}")


class ResourceManager:
    """Tracks per-lane resource budgets and consumption."""

    def __init__(self) -> None:
        self._budgets: Dict[str, ResourceBudget] = {}
        self._lock = threading.RLock()
        self._history: Dict[str, Dict[str, float]] = {}

    def configure_lane(
        self,
        lane: str,
        *,
        cpu_seconds: float = 1.0,
        memory_bytes: int = 64 * 1024 * 1024,
    ) -> ResourceBudget:
        with self._lock:
            budget = ResourceBudget(cpu_seconds, memory_bytes, lane)
            self._budgets[lane] = budget
            self._history.setdefault(lane, {"cpu": 0.0, "memory": 0.0, "timestamp": time.time()})
            _LOGGER.debug(
                "Configured lane %s with cpu=%.3fs memory=%s bytes",
                lane,
                cpu_seconds,
                memory_bytes,
            )
            return budget

    def record_cpu(self, lane: str, seconds: float) -> None:
        with self._lock:
            budget = self._budgets[lane]
            budget.consume_cpu(seconds)
            self._history[lane]["cpu"] += seconds
            self._history[lane]["timestamp"] = time.time()
            _LOGGER.debug("Lane %s consumed %.6fs cpu", lane, seconds)

    def record_memory(self, lane: str, bytes_count: int) -> None:
        with self._lock:
            budget = self._budgets[lane]
            budget.consume_memory(bytes_count)
            self._history[lane]["memory"] += bytes_count
            self._history[lane]["timestamp"] = time.time()
            _LOGGER.debug("Lane %s consumed %s bytes", lane, bytes_count)

    def snapshot(self) -> Dict[str, Dict[str, float]]:
        with self._lock:
            return {lane: dict(stats) for lane, stats in self._history.items()}


__all__ = ["ResourceBudget", "ResourceManager"]
