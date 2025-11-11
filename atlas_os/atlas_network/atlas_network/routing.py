"""Routing table used by network stack."""

from __future__ import annotations

import heapq
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass(order=True)
class RouteEntry:
    sort_score: float
    node_id: str = field(compare=False)
    host: str = field(compare=False)
    port: int = field(compare=False)
    priority: int = field(compare=False)
    last_seen: float = field(compare=False)
    latency_ms: float = field(default=1.0, compare=False)
    packet_loss: float = field(default=0.0, compare=False)
    bandwidth_mbps: float = field(default=100.0, compare=False)


@dataclass
class LinkMetrics:
    latency_ms: float
    packet_loss: float
    bandwidth_mbps: float
    hops: int
    updated_at: float

    def weight(self) -> float:
        latency = self.latency_ms
        loss_penalty = self.packet_loss * 200.0
        bandwidth_penalty = 200.0 / max(self.bandwidth_mbps, 1.0)
        hop_penalty = (self.hops - 1) * 10.0
        return latency + loss_penalty + bandwidth_penalty + hop_penalty


class RoutingTable:
    """Maintain node entries and weighted links for routing decisions."""

    def __init__(self) -> None:
        self._entries: Dict[str, RouteEntry] = {}
        self._links: Dict[str, Dict[str, LinkMetrics]] = defaultdict(dict)
        self._decay_half_life = 45.0

    # ------------------------------------------------------------------
    def _score_entry(
        self,
        *,
        priority: int,
        latency_ms: float,
        packet_loss: float,
        bandwidth_mbps: float,
        last_seen: float,
    ) -> float:
        age_seconds = max(0.0, time.time() - last_seen)
        if self._decay_half_life:
            age_penalty = age_seconds / self._decay_half_life
        else:
            age_penalty = 0.0
        loss_penalty = packet_loss * 300.0
        bandwidth_penalty = 150.0 / max(bandwidth_mbps, 1.0)
        latency_penalty = latency_ms
        priority_bonus = priority * 12.0
        return latency_penalty + loss_penalty + bandwidth_penalty + age_penalty - priority_bonus

    # ------------------------------------------------------------------
    def update(
        self,
        node_id: str,
        host: str,
        port: int,
        *,
        priority: int = 5,
        latency_ms: float = 1.0,
        packet_loss: float = 0.0,
        bandwidth_mbps: float = 100.0,
    ) -> None:
        last_seen = time.time()
        score = self._score_entry(
            priority=priority,
            latency_ms=latency_ms,
            packet_loss=packet_loss,
            bandwidth_mbps=bandwidth_mbps,
            last_seen=last_seen,
        )
        entry = RouteEntry(
            score,
            node_id,
            host,
            port,
            priority,
            last_seen,
            latency_ms,
            packet_loss,
            bandwidth_mbps,
        )
        self._entries[node_id] = entry

    def update_link(
        self,
        source: str,
        target: str,
        *,
        latency_ms: float,
        packet_loss: float = 0.0,
        bandwidth_mbps: float = 100.0,
        hops: int = 1,
    ) -> None:
        metrics = LinkMetrics(latency_ms, packet_loss, bandwidth_mbps, hops, time.time())
        self._links[source][target] = metrics

    # ------------------------------------------------------------------
    def remove(self, node_id: str) -> None:
        self._entries.pop(node_id, None)
        self._links.pop(node_id, None)
        for edges in self._links.values():
            edges.pop(node_id, None)

    def reap_stale(self, ttl: float) -> None:
        threshold = time.time() - ttl
        stale = [node_id for node_id, entry in self._entries.items() if entry.last_seen < threshold]
        for node_id in stale:
            self.remove(node_id)

    def best_route(self) -> Optional[RouteEntry]:
        if not self._entries:
            return None
        return min(self._entries.values())

    def to_list(self) -> List[RouteEntry]:
        return sorted(self._entries.values())

    # ------------------------------------------------------------------
    def _neighbors(self, node_id: str) -> Iterable[Tuple[str, LinkMetrics]]:
        return list(self._links.get(node_id, {}).items())

    def compute_path(self, source: str, destination: str) -> List[str]:
        if source == destination:
            return [source]
        if source not in self._entries or destination not in self._entries:
            raise KeyError("Unknown source or destination node")

        queue: List[Tuple[float, str, List[str]]] = []
        heapq.heappush(queue, (0.0, source, [source]))
        visited: Dict[str, float] = {}

        while queue:
            cost, node, path = heapq.heappop(queue)
            if node == destination:
                return path
            if node in visited and cost >= visited[node]:
                continue
            visited[node] = cost
            for neighbor, metrics in self._neighbors(node):
                weight = metrics.weight()
                next_cost = cost + weight
                if neighbor in visited and next_cost >= visited[neighbor]:
                    continue
                heapq.heappush(queue, (next_cost, neighbor, path + [neighbor]))

        raise RuntimeError(f"No route from {source} to {destination}")

    def snapshot(self) -> Dict[str, Dict[str, float]]:
        state: Dict[str, Dict[str, float]] = {}
        for node_id, entry in self._entries.items():
            state[node_id] = {
                "host": entry.host,
                "port": entry.port,
                "priority": entry.priority,
                "latency_ms": entry.latency_ms,
                "packet_loss": entry.packet_loss,
                "bandwidth_mbps": entry.bandwidth_mbps,
                "last_seen": entry.last_seen,
            }
        return state


__all__ = ["RoutingTable", "RouteEntry", "LinkMetrics"]
