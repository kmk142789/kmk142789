"""Shortest path computation over routing table."""
from __future__ import annotations

import heapq
from typing import Dict, List, Tuple

from .registry import NodeRegistry
from .routing import RoutingTable


class Pathfinder:
    def __init__(self, registry: NodeRegistry, routing: RoutingTable):
        self.registry = registry
        self.routing = routing

    def best_path(self, source_id: str, dest_id: str) -> List[str]:
        distances: Dict[str, float] = {source_id: 0.0}
        queue: List[Tuple[float, str, List[str]]] = [(0.0, source_id, [source_id])]
        visited = set()

        while queue:
            cost, node_id, path = heapq.heappop(queue)
            if node_id in visited:
                continue
            visited.add(node_id)
            if node_id == dest_id:
                return path

            for candidate in self.registry.list():
                if candidate.id == node_id:
                    continue
                weight = self.routing.weight(node_id, candidate.id)
                new_cost = cost + (1.0 / max(weight, 1e-6))
                if candidate.id not in distances or new_cost < distances[candidate.id]:
                    distances[candidate.id] = new_cost
                    heapq.heappush(queue, (new_cost, candidate.id, path + [candidate.id]))
        raise ValueError(f"No path from {source_id} to {dest_id}")


__all__ = ["Pathfinder"]
