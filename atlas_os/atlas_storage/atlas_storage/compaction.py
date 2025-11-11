"""Log structured compaction planning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(slots=True)
class SegmentMetadata:
    identifier: str
    size_bytes: int
    age_seconds: int
    tombstones: int


class CompactionPlanner:
    def __init__(self, *, size_threshold: int, tombstone_threshold: float) -> None:
        self._size_threshold = size_threshold
        self._tombstone_threshold = tombstone_threshold

    def plan(self, segments: Iterable[SegmentMetadata]) -> List[SegmentMetadata]:
        candidates: List[SegmentMetadata] = []
        for segment in segments:
            if segment.size_bytes < self._size_threshold:
                continue
            if segment.tombstones / max(segment.size_bytes, 1) >= self._tombstone_threshold:
                candidates.append(segment)
        return sorted(candidates, key=lambda seg: (seg.age_seconds, seg.size_bytes), reverse=True)


__all__ = ["CompactionPlanner", "SegmentMetadata"]
