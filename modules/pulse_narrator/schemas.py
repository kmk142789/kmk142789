"""Data structures for Pulse Narrator inputs and outputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Literal, Optional

NarratorStyle = Literal["poem", "log"]


@dataclass
class NarrativeInputs:
    """Minimal data required for composing a narrative."""

    snapshot_id: str
    commit_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    total_events: Optional[int] = None
    channels: Optional[List[str]] = None
    top_prefixes: Optional[List[str]] = None
    index_count: Optional[int] = None


@dataclass
class NarrativeArtifact:
    """Rendered narrative artifact."""

    style: NarratorStyle
    title: str
    body_md: str
    inputs: NarrativeInputs
    sha256: str
    path: Optional[str] = None
