from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Event:
    """Structured event emitted by the OuterLink runtime."""

    name: str
    payload: Dict[str, Any]
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "payload": self.payload,
            "ts": self.ts.isoformat(),
        }


class EventBus:
    """Minimal synchronous event bus for offline-first publishing."""

    def __init__(self, max_history: Optional[int] = None) -> None:
        self._subscribers: List[Callable[[Event], None]] = []
        self._history: List[Event] = []
        self._dropped_events = 0
        self._max_history = max_history

    @property
    def history(self) -> List[Event]:
        return list(self._history)

    def stats(self) -> Dict[str, Optional[int]]:
        """Return retention stats without exposing the internal history list."""

        return {
            "limit": self._max_history,
            "retained": len(self._history),
            "dropped": self._dropped_events,
            "total": len(self._history) + self._dropped_events,
        }

    def subscribe(self, callback: Callable[[Event], None]) -> None:
        self._subscribers.append(callback)

    def emit(self, name: str, payload: Optional[Dict[str, Any]] = None) -> Event:
        event = Event(name=name, payload=payload or {})
        self._history.append(event)
        self._trim_history()
        for callback in self._subscribers:
            callback(event)
        return event

    def _trim_history(self) -> None:
        if self._max_history is None or self._max_history <= 0:
            return

        overflow = len(self._history) - self._max_history
        if overflow <= 0:
            return

        del self._history[0:overflow]
        self._dropped_events += overflow


__all__ = ["Event", "EventBus"]
