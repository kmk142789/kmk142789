"""Telemetry helpers for the Atlas networking stack."""

from __future__ import annotations

import statistics
import threading
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass(slots=True)
class TransferSample:
    timestamp: float
    bytes_sent: int
    latency_ms: float


class NetworkTelemetry:
    def __init__(self, *, window: int = 256) -> None:
        self._window = window
        self._samples: List[TransferSample] = []
        self._lock = threading.RLock()
        self._last_activity = 0.0

    def record(self, bytes_sent: int, latency_ms: float) -> None:
        sample = TransferSample(time.time(), bytes_sent, latency_ms)
        with self._lock:
            self._samples.append(sample)
            if len(self._samples) > self._window:
                self._samples = self._samples[-self._window :]
            self._last_activity = sample.timestamp

    def idle_for(self) -> float:
        with self._lock:
            return max(0.0, time.time() - self._last_activity)

    def summary(self) -> Dict[str, float]:
        with self._lock:
            if not self._samples:
                return {"throughput": 0.0, "avg_latency": 0.0}
            total_bytes = sum(sample.bytes_sent for sample in self._samples)
            duration = self._samples[-1].timestamp - self._samples[0].timestamp or 1.0
            throughput = total_bytes / duration
            latencies = [sample.latency_ms for sample in self._samples]
            p95 = statistics.quantiles(latencies, n=20)[-1] if len(latencies) > 1 else latencies[0]
            return {
                "throughput": throughput,
                "avg_latency": statistics.fmean(latencies),
                "p95_latency": p95,
            }

    def samples(self) -> Iterable[TransferSample]:
        with self._lock:
            return list(self._samples)


__all__ = ["NetworkTelemetry", "TransferSample"]
