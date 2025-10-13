"""Utility helpers for beacon operations."""

from __future__ import annotations

from typing import Dict, Iterable
import time

from echo.beacons.base import Beacon


class RateLimiter:
    """Simple exponential backoff limiter for beacon publishing."""

    def __init__(self, min_interval: float = 300.0) -> None:
        self.last_publish = 0.0
        self.min_interval = max(0.0, min_interval)
        self.backoff = 1.0

    def can_publish(self) -> bool:
        elapsed = time.time() - self.last_publish
        return elapsed >= self.min_interval * self.backoff

    def on_success(self) -> None:
        self.last_publish = time.time()
        self.backoff = max(1.0, self.backoff * 0.9)

    def on_failure(self) -> None:
        self.backoff = min(8.0, self.backoff * 1.5)


def estimate_cost(beacons: Iterable[Beacon], payload_size: int) -> Dict[str, float]:
    """Return a rough monetary estimate for publishing to *beacons*."""

    kilobytes = max(payload_size, 0) / 1024
    cost_table = {
        "gist": 0.0,
        "ipfs": 0.001 * kilobytes,
        "arweave": 0.005 * kilobytes,
        "nostr": 0.0,
        "dns": 0.50,
    }

    estimates: Dict[str, float] = {}
    for beacon in beacons:
        name = beacon.name.split("_")[0]
        estimates[beacon.name] = cost_table.get(name, 0.0)
    return estimates
