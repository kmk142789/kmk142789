"""Adaptive beacon selection strategies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple
import random
import time

from echo.beacons.base import Beacon


@dataclass(slots=True)
class BeaconHealth:
    """Rolling health metrics for a beacon."""

    name: str
    success_rate: float
    latency_ms: float
    last_seen: float
    cost: float


class AdaptiveStrategy:
    """Select beacon sets that optimise for resilience and diversity."""

    def __init__(self, health_window: int = 100) -> None:
        self.health: Dict[str, BeaconHealth] = {}
        self.history: List[Tuple[str, bool, float, float]] = []
        self.health_window = max(1, health_window)

    def record(self, beacon: Beacon, *, success: bool, latency_ms: float, cost: float | None = None) -> None:
        """Record a publish attempt for *beacon*."""

        entry = (beacon.name, success, max(0.0, latency_ms), cost or 1.0)
        self.history.append(entry)
        if len(self.history) > self.health_window:
            self.history.pop(0)

        beacon_entries = [item for item in self.history if item[0] == beacon.name]
        successes = sum(1 for item in beacon_entries if item[1])
        attempts = len(beacon_entries)
        success_rate = successes / attempts if attempts else 0.0
        avg_latency = sum(item[2] for item in beacon_entries) / attempts if attempts else 0.0
        avg_cost = sum(item[3] for item in beacon_entries) / attempts if attempts else 1.0

        self.health[beacon.name] = BeaconHealth(
            name=beacon.name,
            success_rate=max(0.0, min(1.0, success_rate)),
            latency_ms=avg_latency,
            last_seen=time.time(),
            cost=max(avg_cost, 1e-6),
        )

    def select(self, available: Iterable[Beacon], k: int, n: int) -> List[Beacon]:
        """Select *n* beacons from *available* maximising independence and health."""

        available_list = list(available)
        if n <= 0 or not available_list:
            return []
        if len(available_list) <= n:
            return available_list

        scored: List[Tuple[float, Beacon]] = []
        for beacon in available_list:
            default_health = BeaconHealth(beacon.name, 1.0, 100.0, 0.0, 1.0)
            health = self.health.get(beacon.name, default_health)
            independence = self._independence_score(beacon, available_list)
            # latency penalty encourages lower latency beacons while keeping diversity
            latency_penalty = 1.0 / (1.0 + max(0.0, health.latency_ms) / 250.0)
            score = health.success_rate * independence * latency_penalty / max(health.cost, 1e-6)
            scored.append((score, beacon))

        random.shuffle(scored)
        scored.sort(key=lambda item: item[0], reverse=True)
        top = [beacon for _, beacon in scored[:n]]

        # ensure at least k beacons even if scoring returns duplicates due to weighting
        if len(top) < min(n, len(available_list)) and k < len(available_list):
            remaining = [b for b in available_list if b not in top]
            random.shuffle(remaining)
            top.extend(remaining[: max(0, n - len(top))])

        return top[:n]

    def _independence_score(self, beacon: Beacon, pool: Iterable[Beacon]) -> float:
        """Estimate independence of *beacon* relative to *pool*."""

        provider_map = {
            "gist": "github",
            "pages": "github",
            "ipfs": "ipfs",
            "nostr": "nostr",
            "dns": "dns",
            "arweave": "arweave",
        }

        def provider_for(name: str) -> str:
            prefix = name.split("_")[0]
            return provider_map.get(prefix, prefix or "unknown")

        my_provider = provider_for(beacon.name)
        same_provider = sum(1 for item in pool if provider_for(item.name) == my_provider)
        return 1.0 / (1.0 + same_provider * 0.3)
