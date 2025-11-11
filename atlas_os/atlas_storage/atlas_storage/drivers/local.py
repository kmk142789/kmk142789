"""Local filesystem driver for the distributed VFS."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


class LocalFileDriver:
    name = "localFS"

    def __init__(self, root: str) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, path: str) -> Path:
        target = self._root / path.strip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def read(self, path: str) -> bytes:
        return self._resolve(path).read_bytes()

    def write(self, path: str, data: bytes) -> None:
        self._resolve(path).write_bytes(data)

    def list(self, prefix: str = "") -> Iterable[str]:
        base = self._root / prefix
        if base.is_file():
            yield str(base.relative_to(self._root))
            return
        if not base.exists():
            return
        for item in base.rglob("*"):
            if item.is_file():
                yield str(item.relative_to(self._root))

    def delete(self, path: str) -> None:
        target = self._resolve(path)
        if target.exists():
            target.unlink()


__all__ = ["LocalFileDriver"]
