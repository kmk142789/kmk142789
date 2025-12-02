"""Storage backends for ethical telemetry events."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from threading import Lock
from typing import Iterable, List

from .schema import TelemetryEvent


class TelemetryStorage(ABC):
    """Abstract interface for telemetry event storage."""

    @abstractmethod
    def write(self, event: TelemetryEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    def flush(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def read(self) -> Iterable[TelemetryEvent]:
        raise NotImplementedError

    @abstractmethod
    def replace(self, events: Iterable[TelemetryEvent]) -> None:
        """Replace the stored events with the provided iterable."""

        raise NotImplementedError


class InMemoryTelemetryStorage(TelemetryStorage):
    """An in-memory storage backend useful for tests."""

    def __init__(self) -> None:
        self._events: List[TelemetryEvent] = []

    def write(self, event: TelemetryEvent) -> None:
        self._events.append(event)

    def flush(self) -> None:  # noqa: D401 - no-op flush
        """No-op flush for in-memory storage."""

    def read(self) -> Iterable[TelemetryEvent]:
        return list(self._events)

    def replace(self, events: Iterable[TelemetryEvent]) -> None:
        self._events = list(events)


class JsonlTelemetryStorage(TelemetryStorage):
    """Durable storage writing events to JSON Lines files."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: TelemetryEvent) -> None:
        data = event.model_dump(by_alias=True)
        with self._lock:
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(data, default=str) + "\n")

    def flush(self) -> None:
        # Files are flushed on close; syncing is handled by the context manager.
        return None

    def read(self) -> Iterable[TelemetryEvent]:
        if not self.path.exists():
            return []
        events: List[TelemetryEvent] = []
        with self._lock:
            with self.path.open("r", encoding="utf-8") as stream:
                for line in stream:
                    payload = json.loads(line)
                    events.append(TelemetryEvent.model_validate(payload))
        return events

    def replace(self, events: Iterable[TelemetryEvent]) -> None:
        with self._lock:
            temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
            with temp_path.open("w", encoding="utf-8") as stream:
                for event in events:
                    data = event.model_dump(by_alias=True)
                    stream.write(json.dumps(data, default=str) + "\n")
            temp_path.replace(self.path)


__all__ = ["TelemetryStorage", "InMemoryTelemetryStorage", "JsonlTelemetryStorage"]
