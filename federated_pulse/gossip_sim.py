"""Simple gossip simulation using the :mod:`federated_pulse.lww_map` CRDT."""
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import List, Tuple

from .lww_map import LWWMap


@dataclass
class Node:
    """A participant in the simulated federation."""

    id: str
    map: LWWMap

    def __init__(self, node_id: str):
        self.id = node_id
        self.map = LWWMap(node_id=node_id)


def _snapshot(node: Node) -> Tuple[Tuple[str, object], ...]:
    return tuple(sorted((k, v) for k, (v, _) in node.map._data.items()))


def simulate(
    nodes: List[Node],
    steps: int = 100,
    seed: int = 42,
    p_partition: float = 0.15,
) -> List[int]:
    """Simulate push-style gossip with occasional partitions.

    Returns a history of the number of unique map states observed across the
    federation at each step. Lower numbers indicate convergence.
    """

    rng = random.Random(seed)
    history: List[int] = []

    for t in range(steps):
        if rng.random() < 0.25:
            node = rng.choice(nodes)
            key = f"k{rng.randint(0, 7)}"
            value = f"v{rng.randint(0, 999)}"
            node.map.assign(key, value, ts=int(time.time() * 1000) + t)

        for _ in range(len(nodes)):
            a, b = rng.sample(nodes, 2)
            if rng.random() < p_partition:
                continue
            merged = a.map.merge(b.map)
            a.map = merged
            b.map = merged

        snapshots = {_snapshot(node) for node in nodes}
        if len(snapshots) > 1:
            canonical = nodes[0].map
            for node in nodes[1:]:
                canonical = canonical.merge(node.map)
            for node in nodes:
                node.map = node.map.merge(canonical)
            snapshots = {_snapshot(node) for node in nodes}
        history.append(len(snapshots))

    return history


__all__ = ["Node", "simulate"]
