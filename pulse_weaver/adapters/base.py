"""Storage adapter abstractions for Pulse Weaver."""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from sqlite3 import Connection
from typing import Iterator


class PulseWeaverAdapter(ABC):
    """Abstract adapter used to manage database connections."""

    @abstractmethod
    def connect(self) -> Connection:
        """Return a DB-API connection object."""

    @contextmanager
    def context(self) -> Iterator[Connection]:
        """Provide a transactional connection context."""

        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


__all__ = ["PulseWeaverAdapter"]
