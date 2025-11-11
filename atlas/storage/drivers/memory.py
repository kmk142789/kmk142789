"""In-memory storage driver."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from ..receipt import StorageReceipt, compute_digest


@dataclass
class MemoryStorageDriver:
    name: str = "memory"
    _store: Dict[str, bytes] = field(default_factory=dict)

    def put(self, path: str, data: bytes) -> StorageReceipt:
        self._store[path] = data
        return StorageReceipt(self.name, path, compute_digest(data), len(data))

    def get(self, path: str) -> bytes:
        try:
            return self._store[path]
        except KeyError as exc:  # pragma: no cover - defensive
            raise FileNotFoundError(path) from exc

    def delete(self, path: str) -> None:
        self._store.pop(path, None)


__all__ = ["MemoryStorageDriver"]
