"""Simple last-write-wins map used by the federation storage adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, Tuple


@dataclass(frozen=True)
class Dot:
    """Logical timestamp paired with a node identifier."""

    ts: int
    node: str

    def __lt__(self, other: "Dot") -> bool:  # pragma: no cover - dataclass helper
        if not isinstance(other, Dot):
            return NotImplemented
        if self.ts != other.ts:
            return self.ts < other.ts
        return self.node < other.node


class LWWMap:
    """Minimal LWW map for simple replication scenarios."""

    def __init__(self, node_id: str):
        self.node = node_id
        self._data: Dict[str, Tuple[Any, Dot]] = {}

    def set(self, key: str, value: Any, ts: int) -> None:
        """Apply a local update with the given timestamp."""

        dot = Dot(ts=ts, node=self.node)
        current = self._data.get(key)
        if current is None or current[1] < dot:
            self._data[key] = (value, dot)

    def merge(self, items: Iterable[Tuple[str, Tuple[Any, Dot]]]) -> None:
        """Merge an iterable of key/value/dot tuples into the map."""

        for key, (value, dot) in items:
            current = self._data.get(key)
            if current is None or current[1] < dot:
                self._data[key] = (value, dot)

    def get(self, key: str, default: Any | None = None) -> Any | None:
        entry = self._data.get(key)
        if entry is None:
            return default
        return entry[0]

    def items(self) -> Iterator[Tuple[str, Any]]:
        for key, (value, _) in self._data.items():
            yield key, value


__all__ = ["Dot", "LWWMap"]
