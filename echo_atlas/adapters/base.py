"""Storage adapter interfaces for the Echo Atlas graph."""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from sqlite3 import Connection
from typing import Iterator


class AtlasAdapter(ABC):
    """Abstract interface for storage engines."""

    @abstractmethod
    def connect(self) -> Connection:
        """Return a raw DB-API connection."""

    @contextmanager
    def context(self) -> Iterator[Connection]:
        """Provide a transactional connection context manager."""

        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


__all__ = ["AtlasAdapter"]
