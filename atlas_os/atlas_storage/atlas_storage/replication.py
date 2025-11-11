"""Replication helpers for Atlas storage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass(slots=True)
class ReplicaDiff:
    path: str
    action: str
    version: int


class ReplicaSynchronizer:
    def calculate_diff(
        self,
        local_manifest: Dict[str, Tuple[int, str]],
        remote_manifest: Dict[str, Tuple[int, str]],
    ) -> List[ReplicaDiff]:
        diffs: List[ReplicaDiff] = []
        all_paths = set(local_manifest) | set(remote_manifest)
        for path in sorted(all_paths):
            local = local_manifest.get(path)
            remote = remote_manifest.get(path)
            if local is None:
                diffs.append(ReplicaDiff(path, "pull", remote[0] if remote else 0))
            elif remote is None:
                diffs.append(ReplicaDiff(path, "push", local[0]))
            elif local[0] < remote[0]:
                diffs.append(ReplicaDiff(path, "pull", remote[0]))
            elif local[0] > remote[0]:
                diffs.append(ReplicaDiff(path, "push", local[0]))
        return diffs

    def merge(
        self,
        local_manifest: Dict[str, Tuple[int, str]],
        updates: Iterable[Tuple[str, int, str]],
    ) -> Dict[str, Tuple[int, str]]:
        merged = dict(local_manifest)
        for path, version, checksum in updates:
            current = merged.get(path)
            if current is None or version >= current[0]:
                merged[path] = (version, checksum)
        return merged


__all__ = ["ReplicaSynchronizer", "ReplicaDiff"]
