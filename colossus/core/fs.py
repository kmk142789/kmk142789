"""File system helpers used by the Colossus generators."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
import json
import os
import tempfile


@contextmanager
def atomic_write(path: Path, mode: str = "w", encoding: str | None = "utf-8") -> Iterator[object]:
    """Write to ``path`` atomically using a temporary file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix="._colossus")
    os.close(fd)
    tmp = Path(tmp_path)
    try:
        with tmp.open(mode, encoding=encoding) as handle:
            yield handle
        tmp.replace(path)
    finally:
        if tmp.exists():  # pragma: no branch - cleanup
            tmp.unlink()


def write_json(path: Path, payload: dict, *, sort_keys: bool = True) -> None:
    with atomic_write(path) as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=sort_keys)
        handle.write("\n")


@dataclass
class Cursor:
    """Stateful cursor persisted to disk."""

    path: Path

    def load(self) -> str | None:
        if not self.path.exists():
            return None
        return self.path.read_text("utf-8").strip() or None

    def store(self, value: str) -> None:
        with atomic_write(self.path) as handle:
            handle.write(value)


@dataclass
class ManifestWriter:
    """Append-only manifest writer that maintains deterministic ordering."""

    path: Path

    def append(self, record: dict) -> None:
        line = json.dumps(record, sort_keys=True, ensure_ascii=False)
        existing = ""
        if self.path.exists():
            existing = self.path.read_text("utf-8")
        with atomic_write(self.path) as handle:
            if existing:
                handle.write(existing)
            handle.write(line)
            handle.write("\n")


__all__ = [
    "Cursor",
    "ManifestWriter",
    "atomic_write",
    "write_json",
]
