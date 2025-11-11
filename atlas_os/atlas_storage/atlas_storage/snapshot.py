"""Snapshot manager providing point-in-time recovery."""

from __future__ import annotations

import copy
import json
import threading
from typing import Dict

from .vfs import DistributedVirtualFileSystem


class SnapshotManager:
    def __init__(self, vfs: DistributedVirtualFileSystem) -> None:
        self._vfs = vfs
        self._snapshots: Dict[str, Dict[str, bytes]] = {}
        self._lock = threading.RLock()

    def create(self, name: str) -> None:
        snapshot: Dict[str, bytes] = {}
        for path in self._vfs.list():
            snapshot[path] = self._vfs.read(path)
        with self._lock:
            self._snapshots[name] = snapshot

    def rollback(self, name: str) -> None:
        with self._lock:
            snapshot = copy.deepcopy(self._snapshots[name])
        for path in self._vfs.list():
            self._vfs.delete(path)
        for path, data in snapshot.items():
            self._vfs.write(path, data)

    def export(self) -> str:
        with self._lock:
            manifest = {name: sorted(entries.keys()) for name, entries in self._snapshots.items()}
        return json.dumps(manifest, indent=2, sort_keys=True)


__all__ = ["SnapshotManager"]
