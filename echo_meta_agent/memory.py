"""Persistent memory for the Echo Meta Agent."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .types import ToolCallEvent
from .utils import safe_truncate


_MEMORY_PATH = Path(__file__).resolve().parent / "memory.json"


def _ensure_file() -> None:
    if not _MEMORY_PATH.exists():
        _MEMORY_PATH.write_text("[]", encoding="utf-8")


def _read() -> List[Dict[str, Any]]:
    _ensure_file()
    with _MEMORY_PATH.open("r", encoding="utf-8") as handle:
        try:
            return json.load(handle)
        except json.JSONDecodeError:
            return []


def _write(entries: List[Dict[str, Any]]) -> None:
    _MEMORY_PATH.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")


def log(event: Dict[str, Any]) -> None:
    """Persist an event, automatically adding metadata."""

    entries = _read()
    event_copy = dict(event)
    event_copy.setdefault("timestamp", datetime.utcnow().isoformat())
    if "result_summary" not in event_copy and "result" in event_copy:
        event_copy["result_summary"] = safe_truncate(event_copy["result"])
        event_copy.pop("result", None)
    entries.append(event_copy)
    _write(entries)


def log_event(event: ToolCallEvent) -> None:
    """Persist a :class:`ToolCallEvent`."""

    log(event.as_dict())


def last(n: int = 20) -> List[Dict[str, Any]]:
    """Return the most recent *n* events."""

    entries = _read()
    return entries[-n:]


def find(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Return events containing *query* in any value."""

    if not query:
        return []
    query_lower = query.lower()
    matches: List[Dict[str, Any]] = []
    for event in reversed(_read()):
        if len(matches) >= limit:
            break
        if any(query_lower in str(value).lower() for value in event.values()):
            matches.append(event)
    return list(reversed(matches))


__all__ = ["log", "log_event", "last", "find"]
