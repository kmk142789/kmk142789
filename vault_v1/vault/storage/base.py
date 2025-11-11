from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol


class StorageBackend(ABC):
    """Abstract storage backend for chunks."""

    @abstractmethod
    def has_chunk(self, chunk_hash: str) -> bool:  # pragma: no cover - interface
        raise NotImplementedError

    @abstractmethod
    def write_chunk(self, chunk_hash: str, data: bytes) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    @abstractmethod
    def read_chunk(self, chunk_hash: str) -> bytes:  # pragma: no cover - interface
        raise NotImplementedError


class LocalPathProvider(Protocol):
    def resolve_path(self, chunk_hash: str) -> Path:  # pragma: no cover - interface
        ...
