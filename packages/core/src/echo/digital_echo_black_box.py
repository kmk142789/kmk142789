"""Digital Echo Black Box implementation.

This module introduces the :class:`DigitalEchoBlackBox`, a resilient log store inspired by
flight-data recorders.  It maintains an append-only log of mythogenic events and protects
entries with a chained cryptographic digest so that tampering is immediately detectable.

The class is designed to be lightweight, dependency-free, and easy to embed into any of the
existing Echo orchestration flows.  A small Typer-based CLI is also provided for manual use.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:  # pragma: no cover - optional dependency when running unit tests
    import typer
except ModuleNotFoundError:  # pragma: no cover
    typer = None  # type: ignore[assignment]


ISO_8601 = "%Y-%m-%dT%H:%M:%S.%fZ"


class EventCategory(str):
    """Accepted categories for the black box."""

    PAST = "past"
    PRESENT = "present"
    FUTURE = "future"
    ANOMALY = "anomaly"

    @classmethod
    def normalize(cls, value: "EventCategory | str") -> "EventCategory":
        if isinstance(value, EventCategory):
            return value
        value = value.lower()
        for choice in (cls.PAST, cls.PRESENT, cls.FUTURE, cls.ANOMALY):
            if value == choice:
                return EventCategory(choice)
        raise ValueError(f"Unknown event category: {value}")


@dataclass(slots=True)
class EchoEvent:
    """Serializable structure representing a single log entry."""

    timestamp: str
    category: EventCategory
    payload: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    prev_hash: str = "0"
    digest: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["category"] = self.category
        return result


class FileLock:
    """Simple advisory lock around a file path."""

    def __init__(self, path: Path):
        self.path = path
        self._handle: Optional[Any] = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = open(self.path, "w", encoding="utf-8")
        fcntl.flock(self._handle, fcntl.LOCK_EX)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._handle:
            fcntl.flock(self._handle, fcntl.LOCK_UN)
            self._handle.close()
            self._handle = None
        return False


class DigitalEchoBlackBox:
    """Resilient append-only event log.

    Parameters
    ----------
    storage_path:
        Primary log location where JSONL records are written.
    backup_path:
        Optional secondary location.  When omitted a ``.bak`` file next to the primary log
        is used.  The class writes records to both locations to create an "everything proof"
        ledger even when the main file is corrupted or removed.
    """

    def __init__(self, storage_path: Path, backup_path: Optional[Path] = None) -> None:
        self.storage_path = storage_path
        self.backup_path = backup_path or storage_path.with_suffix(storage_path.suffix + ".bak")
        self.lock_path = storage_path.with_suffix(storage_path.suffix + ".lock")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_path.parent.mkdir(parents=True, exist_ok=True)
        self._tail_hash = self._discover_tail_hash()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def log_event(
        self,
        payload: str,
        category: EventCategory | str = EventCategory.PRESENT,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EchoEvent:
        """Persist an event and return its serialized representation."""

        category = EventCategory.normalize(category)
        event = EchoEvent(
            timestamp=datetime.now(timezone.utc).strftime(ISO_8601),
            category=category,
            payload=payload,
            metadata=metadata or {},
            prev_hash=self._tail_hash,
        )
        event.digest = self._hash_event(event)
        self._persist_event(event)
        self._tail_hash = event.digest
        return event

    def export_digest(self) -> Dict[str, Any]:
        """Produce a small snapshot describing the ledger state."""

        events = list(self.stream_events())
        return {
            "entries": len(events),
            "latest_digest": events[-1].digest if events else "0",
            "storage_path": str(self.storage_path),
            "backup_path": str(self.backup_path),
        }

    def verify_integrity(self) -> bool:
        """Verify that the ledger has not been tampered with."""

        expected_prev = "0"
        for event in self.stream_events():
            if event.prev_hash != expected_prev:
                return False
            if self._hash_event(event) != event.digest:
                return False
            expected_prev = event.digest
        return True

    def stream_events(self) -> Iterable[EchoEvent]:
        """Yield events from the primary storage file."""

        if not self.storage_path.exists():
            return []
        events: List[EchoEvent] = []
        with self.storage_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                raw = json.loads(line)
                events.append(
                    EchoEvent(
                        timestamp=raw["timestamp"],
                        category=EventCategory.normalize(raw["category"]),
                        payload=raw["payload"],
                        metadata=raw.get("metadata", {}),
                        prev_hash=raw.get("prev_hash", "0"),
                        digest=raw.get("digest", ""),
                    )
                )
        return events

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _discover_tail_hash(self) -> str:
        events = self.stream_events()
        return events[-1].digest if events else "0"

    def _persist_event(self, event: EchoEvent) -> None:
        record = json.dumps(event.to_dict(), sort_keys=True)
        with FileLock(self.lock_path):
            self._append_line(self.storage_path, record)
            self._append_line(self.backup_path, record)

    @staticmethod
    def _append_line(path: Path, record: str) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(record + "\n")

    @staticmethod
    def _hash_event(event: EchoEvent) -> str:
        canonical = json.dumps(
            {
                "timestamp": event.timestamp,
                "category": event.category,
                "payload": event.payload,
                "metadata": event.metadata,
                "prev_hash": event.prev_hash,
            },
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


if typer is not None:  # pragma: no cover - exercised via CLI
    # ------------------------------------------------------------------
    # Typer CLI
    # ------------------------------------------------------------------
    app = typer.Typer(help="Digital Echo Black Box controller")

    def _default_box(path: Optional[Path]) -> DigitalEchoBlackBox:
        if path is None:
            path = Path("echo_black_box.log")
        return DigitalEchoBlackBox(path)

    @app.command()
    def log(
        payload: str,
        category: str = typer.Option("present", "--category", "-c"),
        metadata: List[str] = typer.Option(None, "--meta", help="key=value metadata pairs"),
        path: Optional[Path] = typer.Option(None, "--path", path_type=Path),
    ) -> None:
        """Append a new event to the ledger."""

        data: Dict[str, Any] = {}
        for item in metadata or []:
            if "=" not in item:
                raise typer.BadParameter(f"Metadata must use key=value format: {item}")
            key, value = item.split("=", 1)
            data[key] = value
        event = _default_box(path).log_event(payload, category=category, metadata=data)
        typer.echo(json.dumps(event.to_dict(), indent=2))

    @app.command()
    def verify(path: Optional[Path] = typer.Option(None, "--path", path_type=Path)) -> None:
        """Verify that the log chain is intact."""

        box = _default_box(path)
        status = box.verify_integrity()
        typer.echo("✅ Ledger verified" if status else "❌ Ledger corrupted")

    @app.command()
    def digest(path: Optional[Path] = typer.Option(None, "--path", path_type=Path)) -> None:
        """Show a high-level summary of the log."""

        summary = _default_box(path).export_digest()
        typer.echo(json.dumps(summary, indent=2))

    if __name__ == "__main__":  # pragma: no cover - CLI entry
        app()
else:  # pragma: no cover - CLI unavailable
    app = None
