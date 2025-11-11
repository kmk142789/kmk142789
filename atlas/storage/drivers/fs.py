"""File system storage driver."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..receipt import StorageReceipt, compute_digest


@dataclass
class FileSystemDriver:
    base_path: Path
    name: str = "fs"

    def __post_init__(self) -> None:
        self.base_path.mkdir(parents=True, exist_ok=True)

    def put(self, path: str, data: bytes) -> StorageReceipt:
        destination = self.base_path / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return StorageReceipt(self.name, str(destination.relative_to(self.base_path)), compute_digest(data), len(data))

    def get(self, path: str) -> bytes:
        data = (self.base_path / path).read_bytes()
        return data

    def delete(self, path: str) -> None:
        target = self.base_path / path
        if target.exists():
            target.unlink()


__all__ = ["FileSystemDriver"]
