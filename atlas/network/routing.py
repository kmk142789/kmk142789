"""Weighted routing table with decay-aware updates."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple

from .registry import NodeInfo


@dataclass
class RoutingTable:
    weights: Dict[Tuple[str, str], float] = field(default_factory=dict)

    def update(self, source: NodeInfo, dest: NodeInfo, weight: float) -> None:
        key = (source.id, dest.id)
        current = self.weights.get(key, 0.5)
        new_weight = (current * 0.7) + (weight * 0.3)
        self.weights[key] = max(0.0, min(1.0, new_weight))

    def weight(self, source_id: str, dest_id: str) -> float:
        return self.weights.get((source_id, dest_id), 0.5)


__all__ = ["RoutingTable"]
