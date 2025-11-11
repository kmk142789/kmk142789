"""Storage driver interface."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from ..receipt import StorageReceipt


class StorageDriver(Protocol):
    name: str

    def put(self, path: str, data: bytes) -> StorageReceipt:
        ...

    def get(self, path: str) -> bytes:
        ...

    def delete(self, path: str) -> None:
        ...


__all__ = ["StorageDriver"]
