"""Capability planning logic."""

from __future__ import annotations

from collections import deque
from typing import Dict, List, Set

from .model import CapState, Capability


def plan_install(target: Capability, catalog: Dict[str, Capability], state: CapState) -> List[Capability]:
    """Return an ordered installation plan for ``target`` respecting dependencies."""

    order: List[Capability] = []
    seen: Set[str] = set()
    queue = deque([target.name])

    def enqueue(name: str) -> None:
        if name in seen or state.has(name):
            return
        seen.add(name)
        if name not in catalog:
            raise KeyError(f"Unknown capability: {name}")
        capability = catalog[name]
        for dep in sorted(capability.requires, reverse=True):
            enqueue(dep)
        order.append(capability)

    while queue:
        enqueue(queue.popleft())

    return [cap for cap in order if not state.has(cap.name)]


__all__ = ["plan_install"]
