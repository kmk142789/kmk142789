from __future__ import annotations

from pathlib import Path

from .base import StorageBackend


class LocalFileStorage(StorageBackend):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _chunk_path(self, chunk_hash: str) -> Path:
        prefix = chunk_hash[:2]
        folder = self.root / prefix
        folder.mkdir(exist_ok=True)
        return folder / chunk_hash

    def has_chunk(self, chunk_hash: str) -> bool:
        return self._chunk_path(chunk_hash).exists()

    def write_chunk(self, chunk_hash: str, data: bytes) -> None:
        path = self._chunk_path(chunk_hash)
        if not path.exists():
            path.write_bytes(data)

    def read_chunk(self, chunk_hash: str) -> bytes:
        path = self._chunk_path(chunk_hash)
        if not path.exists():  # pragma: no cover - defensive
            raise FileNotFoundError(chunk_hash)
        return path.read_bytes()


__all__ = ["LocalFileStorage"]
