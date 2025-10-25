"""Schema helpers for Atlas federation reports."""

from __future__ import annotations

from typing import List, TypedDict


class CycleTimelineEvent(TypedDict):
    """Minimal shape describing a cycle timeline event."""

    cycle: int
    entry_count: int
    puzzle_ids: List[int]
    harmonics: List[int]


__all__ = ["CycleTimelineEvent"]
