"""Filesystem adapter utilities."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class FileSnapshot:
    """Represents a captured filesystem state for rollback support."""

    path: Path
    exists: bool
    content: Optional[bytes]


class FileSystemAdapter:
    """Minimal filesystem abstraction used by Dominion executors."""

    def __init__(self, root: Path | str = ".") -> None:
        self.root = Path(root).resolve()

    def resolve(self, target: str | Path) -> Path:
        path = Path(target)
        if not path.is_absolute():
            path = self.root / path
        return path

    def snapshot(self, target: str | Path) -> FileSnapshot:
        path = self.resolve(target)
        if path.exists():
            return FileSnapshot(path=path, exists=True, content=path.read_bytes())
        return FileSnapshot(path=path, exists=False, content=None)

    def restore(self, snapshot: FileSnapshot) -> None:
        if snapshot.exists:
            snapshot.path.parent.mkdir(parents=True, exist_ok=True)
            if snapshot.content is not None:
                snapshot.path.write_bytes(snapshot.content)
        elif snapshot.path.exists():
            snapshot.path.unlink()

    def write_text(self, target: str | Path, content: str) -> None:
        path = self.resolve(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def read_text(self, target: str | Path) -> str:
        path = self.resolve(target)
        return path.read_text(encoding="utf-8")

    def write_json(self, target: str | Path, payload: Dict[str, Any], *, indent: int = 2) -> None:
        path = self.resolve(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=indent, sort_keys=True), encoding="utf-8")

    def read_json(self, target: str | Path) -> Dict[str, Any]:
        path = self.resolve(target)
        return json.loads(path.read_text(encoding="utf-8"))

    def exists(self, target: str | Path) -> bool:
        return self.resolve(target).exists()

