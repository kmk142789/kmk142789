"""Schema helpers for Atlas federation reports."""

from __future__ import annotations

from typing import List, NotRequired, TypedDict


class CycleTimelineEvent(TypedDict):
    """Shape describing a cycle timeline event with harmonic annotations."""

    cycle: int
    entry_count: int
    puzzle_ids: List[int]
    harmonics: List[float]
    normalized_harmonics: NotRequired[List[float]]
    harmonic_average: NotRequired[float | None]
    harmonic_min: NotRequired[float | None]
    harmonic_max: NotRequired[float | None]


__all__ = ["CycleTimelineEvent"]
