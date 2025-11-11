"""Write-ahead journal for storage operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Mapping


class WriteAheadJournal:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def append(self, record: Mapping[str, object]) -> None:
        line = json.dumps(record, sort_keys=True)
        with self._path.open("a", encoding="utf8") as handle:
            handle.write(line + "\n")

    def replay(self) -> List[Mapping[str, object]]:
        entries: List[Mapping[str, object]] = []
        with self._path.open("r", encoding="utf8") as handle:
            for line in handle:
                entries.append(json.loads(line))
        return entries

    def truncate(self) -> None:
        self._path.write_text("", encoding="utf8")

    def stream(self) -> Iterable[Mapping[str, object]]:
        with self._path.open("r", encoding="utf8") as handle:
            for line in handle:
                yield json.loads(line)


__all__ = ["WriteAheadJournal"]
