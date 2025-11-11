"""Metrics exporter for kernel subsystems."""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass
from typing import Dict, Iterable

_LOGGER = logging.getLogger(__name__)


@dataclass
class MetricSample:
    name: str
    value: float
    timestamp: float


class KernelMetricsExporter:
    """Collects metrics and exposes them as JSON snapshots."""

    def __init__(self) -> None:
        self._samples: Dict[str, MetricSample] = {}
        self._lock = threading.RLock()

    def record(self, name: str, value: float) -> None:
        with self._lock:
            self._samples[name] = MetricSample(name, float(value), time.time())
            _LOGGER.debug("Metric recorded %s=%s", name, value)

    def export(self) -> str:
        with self._lock:
            payload = {name: sample.__dict__ for name, sample in self._samples.items()}
        return json.dumps(payload, sort_keys=True)

    def stream(self) -> Iterable[MetricSample]:
        with self._lock:
            for sample in self._samples.values():
                yield sample


__all__ = ["KernelMetricsExporter", "MetricSample"]
