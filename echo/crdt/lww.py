"""Last-write-wins map implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Tuple


@dataclass(frozen=True)
class Clock:
    """Logical clock tagging each mutation."""

    node: str
    tick: int

    def __lt__(self, other: "Clock") -> bool:  # pragma: no cover - dataclass order helper
        if not isinstance(other, Clock):
            return NotImplemented
        if self.tick != other.tick:
            return self.tick < other.tick
        return self.node < other.node


class LWWMap:
    """Clocked last-write-wins map suitable for CRDT replication."""

    def __init__(self, node_id: str) -> None:
        self.node = node_id
        self.data: Dict[str, Tuple[Clock, Any]] = {}
        self._ticks: Dict[str, int] = {}

    def set(self, key: str, value: Any) -> None:
        next_tick = self._ticks.get(key, 0) + 1
        self._ticks[key] = next_tick
        self.data[key] = (Clock(node=self.node, tick=next_tick), value)

    def merge(self, other: "LWWMap | Mapping[str, Tuple[Clock, Any]]") -> None:
        if isinstance(other, LWWMap):
            items: Iterable[Tuple[str, Tuple[Clock, Any]]] = other.data.items()
        elif isinstance(other, Mapping):
            items = other.items()
        else:
            raise TypeError("LWWMap.merge expects another LWWMap or mapping")

        for key, (clock, value) in items:
            current = self.data.get(key)
            if current is None or current[0] < clock:
                self.data[key] = (clock, value)
                if clock.node == self.node:
                    self._ticks[key] = max(self._ticks.get(key, 0), clock.tick)

    def snapshot(self) -> Dict[str, Any]:
        return {key: value for key, (_, value) in self.data.items()}

    def state(self) -> Dict[str, Tuple[Clock, Any]]:
        """Expose the full CRDT state for replication."""

        return dict(self.data)


__all__ = ["Clock", "LWWMap"]
