"""In-process metrics registry supporting counters and timers."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from statistics import mean
from typing import Dict, List


@dataclass
class Counter:
    name: str
    value: int = 0

    def inc(self, amount: int = 1) -> None:
        self.value += amount


@dataclass
class Timer:
    name: str
    samples: List[float] = field(default_factory=list)

    def observe(self, value: float) -> None:
        self.samples.append(value)

    def summary(self) -> Dict[str, float]:
        data = self.samples or [0.0]
        return {"count": float(len(data)), "avg": mean(data), "max": max(data)}


class MetricsRegistry:
    def __init__(self) -> None:
        self._counters: Dict[str, Counter] = {}
        self._timers: Dict[str, Timer] = {}
        self._lock = asyncio.Lock()

    async def counter(self, name: str) -> Counter:
        async with self._lock:
            return self._counters.setdefault(name, Counter(name))

    async def timer(self, name: str) -> Timer:
        async with self._lock:
            return self._timers.setdefault(name, Timer(name))

    async def export_prometheus(self) -> str:
        lines: List[str] = []
        async with self._lock:
            for counter in self._counters.values():
                lines.append(f"# TYPE {counter.name} counter")
                lines.append(f"{counter.name} {counter.value}")
            for timer in self._timers.values():
                summary = timer.summary()
                lines.append(f"# TYPE {timer.name} summary")
                for key, value in summary.items():
                    lines.append(f"{timer.name}_{key} {value}")
        return "\n".join(lines) + "\n"

    async def snapshot(self) -> Dict[str, object]:
        async with self._lock:
            return {
                "counters": {name: counter.value for name, counter in self._counters.items()},
                "timers": {name: timer.summary() for name, timer in self._timers.items()},
            }


__all__ = ["MetricsRegistry", "Counter", "Timer"]
