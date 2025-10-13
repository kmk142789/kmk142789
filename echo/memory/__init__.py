"""JSON-backed ledger utilities for Echo's memory layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, MutableMapping

import json


@dataclass(slots=True)
class MemoryLedger:
    """Persist a chronological ledger of Echo state transitions."""

    path: Path
    entries: List[MutableMapping[str, object]] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path | str) -> "MemoryLedger":
        path = Path(path)
        if path.exists():
            try:
                payload = json.loads(path.read_text())
                entries = [entry for entry in payload if isinstance(entry, dict)]
            except (json.JSONDecodeError, OSError, TypeError):
                entries = []
        else:
            entries = []
        return cls(path=path, entries=list(entries))

    def persist(self, entry: MutableMapping[str, object]) -> None:
        """Append *entry* to the ledger and flush to disk."""

        entry.setdefault("timestamp", self._timestamp())
        self.entries.append(entry)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.entries, indent=2))

    def extend(self, entries: Iterable[MutableMapping[str, object]]) -> None:
        for entry in entries:
            self.persist(entry)

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()


__all__ = ["MemoryLedger"]
