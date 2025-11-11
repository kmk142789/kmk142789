"""Integrity checking utilities for the storage subsystem."""

from __future__ import annotations

import hashlib
import json
from typing import Dict, Iterable

from .vfs import DistributedVirtualFileSystem


class IntegrityChecker:
    def __init__(self, vfs: DistributedVirtualFileSystem) -> None:
        self._vfs = vfs

    def _digest(self, data: bytes) -> str:
        hasher = hashlib.sha256()
        hasher.update(data)
        return hasher.hexdigest()

    def manifest(self, paths: Iterable[str] | None = None) -> Dict[str, str]:
        manifest: Dict[str, str] = {}
        for path in paths or self._vfs.list():
            manifest[path] = self._digest(self._vfs.read(path))
        return manifest

    def verify(self, manifest: Dict[str, str]) -> bool:
        for path, expected in manifest.items():
            if self._digest(self._vfs.read(path)) != expected:
                return False
        return True

    def export(self, manifest: Dict[str, str]) -> str:
        return json.dumps(manifest, indent=2, sort_keys=True)


__all__ = ["IntegrityChecker"]
