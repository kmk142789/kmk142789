"""Append-only transaction log for storage operations."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional


@dataclass
class Transaction:
    timestamp: float
    action: str
    payload: Dict


class TransactionLog:
    """Stores structured transaction entries in memory and on disk."""

    def __init__(self, path: Optional[str] = None) -> None:
        self._path = Path(path) if path else None
        self._entries: list[Transaction] = []
        self._lock = threading.RLock()
        if self._path:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            if self._path.exists():
                for line in self._path.read_text().splitlines():
                    timestamp, action, payload_json = line.split("|", 2)
                    self._entries.append(
                        Transaction(float(timestamp), action, json.loads(payload_json))
                    )

    def append(self, action: str, payload: Dict) -> Transaction:
        entry = Transaction(time.time(), action, dict(payload))
        with self._lock:
            self._entries.append(entry)
            if self._path:
                with self._path.open("a", encoding="utf8") as fh:
                    fh.write(f"{entry.timestamp}|{action}|{json.dumps(payload, sort_keys=True)}\n")
        return entry

    def tail(self, limit: int = 20) -> Iterable[Transaction]:
        with self._lock:
            return list(self._entries[-limit:])

    def __iter__(self):
        with self._lock:
            return iter(list(self._entries))


__all__ = ["Transaction", "TransactionLog"]
