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

    def __init__(self) -> None:
        self._subscribers: List[Callable[[Event], None]] = []
        self._history: List[Event] = []

    @property
    def history(self) -> List[Event]:
        return list(self._history)

    def subscribe(self, callback: Callable[[Event], None]) -> None:
        self._subscribers.append(callback)

    def emit(self, name: str, payload: Optional[Dict[str, Any]] = None) -> Event:
        event = Event(name=name, payload=payload or {})
        self._history.append(event)
        for callback in self._subscribers:
            callback(event)
        return event


__all__ = ["Event", "EventBus"]
