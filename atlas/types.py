"""Shared TypedDict definitions for Atlas federation helpers."""

from __future__ import annotations

from typing import List, TypedDict


class Entry(TypedDict, total=False):
    cycle: int
    puzzle_id: int
    address: str
    title: str
    digest: str
    source: str
    tags: List[str]
    lineage: List[int]
    updated_at: str
    script: str
    harmonics: List[int]
