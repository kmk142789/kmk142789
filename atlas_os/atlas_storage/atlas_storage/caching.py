"""In-memory caching layer for hot segments."""

from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Generic, MutableMapping, Optional, TypeVar


K = TypeVar("K")
V = TypeVar("V")


@dataclass(slots=True)
class CacheEntry(Generic[V]):
    value: V
    expires_at: float


class SegmentCache(Generic[K, V]):
    def __init__(self, capacity: int, *, ttl: float) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self._store: "OrderedDict[K, CacheEntry[V]]" = OrderedDict()
        self._capacity = capacity
        self._ttl = ttl

    def put(self, key: K, value: V) -> None:
        expires_at = time.time() + self._ttl
        if key in self._store:
            self._store.pop(key)
        elif len(self._store) >= self._capacity:
            self._store.popitem(last=False)
        self._store[key] = CacheEntry(value, expires_at)

    def get(self, key: K) -> Optional[V]:
        entry = self._store.get(key)
        if not entry:
            return None
        if entry.expires_at < time.time():
            self._store.pop(key, None)
            return None
        self._store.move_to_end(key)
        return entry.value

    def snapshot(self) -> MutableMapping[K, V]:
        now = time.time()
        return {key: entry.value for key, entry in self._store.items() if entry.expires_at >= now}


__all__ = ["SegmentCache", "CacheEntry"]
