"""Minimal Last-Write-Wins (LWW) Map CRDT implementation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, MutableMapping, Optional, Tuple

Timestamp = int


@dataclass(frozen=True)
class Dot:
    """Unique identifier for a map mutation."""

    ts: Timestamp
    node: str


class LWWMap(MutableMapping[str, Any]):
    """Last-Write-Wins Map CRDT.

    The map keeps the value for a key that has the highest ``(timestamp, node)``
    pair in lexicographic order. This ensures deterministic, idempotent and
    commutative merges across replicas.
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self._data: Dict[str, Tuple[Any, Dot]] = {}

    # -- MutableMapping API -------------------------------------------------
    def __getitem__(self, key: str) -> Any:  # type: ignore[override]
        value = self.get(key)
        if value is None and key not in self._data:
            raise KeyError(key)
        return value

    def __setitem__(self, key: str, value: Any) -> None:  # type: ignore[override]
        self.assign(key, value, ts=self._clock())

    def __delitem__(self, key: str) -> None:  # type: ignore[override]
        if key not in self._data:
            raise KeyError(key)
        self.remove(key, ts=self._clock())

    def __iter__(self) -> Iterator[str]:  # type: ignore[override]
        return iter(self._data)

    def __len__(self) -> int:  # type: ignore[override]
        return len(self._data)

    # ----------------------------------------------------------------------
    def _clock(self) -> Timestamp:
        """Return a monotonic-ish timestamp for ad-hoc mutations."""

        import time

        return int(time.time() * 1000)

    def assign(self, key: str, value: Any, ts: Timestamp) -> None:
        """Assign ``value`` to ``key`` with timestamp ``ts``."""

        dot = Dot(ts=ts, node=self.node_id)
        current = self._data.get(key)
        if current is None or (dot.ts, dot.node) > (current[1].ts, current[1].node):
            self._data[key] = (value, dot)

    def remove(self, key: str, ts: Timestamp) -> None:
        """Logically delete ``key`` by recording a tombstone entry."""

        self.assign(key, None, ts)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Return the value for ``key`` or ``default`` if missing."""

        entry = self._data.get(key)
        if entry is None:
            return default
        return entry[0]

    def state(self) -> Dict[str, Tuple[Any, Tuple[Timestamp, str]]]:
        """Return a serialisable copy of the map state."""

        return {
            key: (value, (dot.ts, dot.node))
            for key, (value, dot) in self._data.items()
        }

    def merge(self, other: "LWWMap") -> "LWWMap":
        """Merge this replica with ``other`` and return the result."""

        merged = LWWMap(self.node_id)
        merged._data = self._data.copy()
        for key, (oval, odot) in other._data.items():
            current = merged._data.get(key)
            if current is None or (odot.ts, odot.node) > (current[1].ts, current[1].node):
                merged._data[key] = (oval, odot)
        return merged

    # Convenience helpers --------------------------------------------------
    def keys(self) -> List[str]:  # type: ignore[override]
        return list(self._data.keys())

    def items(self) -> List[Tuple[str, Any]]:
        return [(key, value) for key, (value, _) in self._data.items()]

    def values(self) -> List[Any]:
        return [value for value, _ in self._data.values()]

    def copy(self) -> "LWWMap":
        replica = LWWMap(self.node_id)
        replica._data = self._data.copy()
        return replica


__all__ = ["Timestamp", "Dot", "LWWMap"]
