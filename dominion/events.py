"""Event primitives for Dominion journaling."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class JournalEntry:
    intent_id: str
    action_type: str
    status: str
    message: str
    timestamp: str = field(default_factory=utc_now_iso)


@dataclass
class DominionReceipt:
    plan_id: str
    applied_at: str
    status: str
    summary: Dict[str, Any]


@dataclass
class DominionJournal:
    plan_id: str
    entries: list[JournalEntry]
    created_at: str = field(default_factory=utc_now_iso)

