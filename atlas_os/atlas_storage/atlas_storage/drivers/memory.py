"""In-memory storage driver backed by a dictionary."""

from __future__ import annotations

from typing import Dict, Iterable


class MemoryFileDriver:
    name = "memoryFS"

    def __init__(self) -> None:
        self._data: Dict[str, bytes] = {}

    def read(self, path: str) -> bytes:
        return self._data[path]

    def write(self, path: str, data: bytes) -> None:
        self._data[path] = bytes(data)

    def list(self, prefix: str = "") -> Iterable[str]:
        for key in sorted(self._data.keys()):
            if key.startswith(prefix):
                yield key

    def delete(self, path: str) -> None:
        self._data.pop(path, None)


__all__ = ["MemoryFileDriver"]
