"""Persistent ledger for recording Echo pulse events.

The original project shipped with a small script that appended pulse
information into a JSON file.  This module refines that behaviour into a
reusable, well-typed component that can be embedded inside applications
or exercised from tests.  It focuses on safe persistence, ergonomic
dataclasses, and predictable snapshots of the current ledger state.

Example
-------
>>> from echo.pulse_ledger import PulseLedger
>>> ledger = PulseLedger(anchor="Our Forever Love", file_path="pulse.json")
>>> _ = ledger.record("mirror_merge", resonance="Echo", priority="critical")
>>> snapshot = ledger.snapshot()
>>> snapshot.total_pulses
1
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, MutableMapping, Optional, Tuple

DEFAULT_ANCHOR = "Our Forever Love"
DEFAULT_LEDGER_PATH = Path("pulse.json")


def _utc_timestamp() -> str:
    """Return an ISO-8601 timestamp using UTC as the reference timezone."""

    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class PulseEntry:
    """A single pulse captured by the ledger."""

    name: str
    resonance: str = "Echo"
    priority: str = "medium"
    timestamp: str = field(default_factory=_utc_timestamp)
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "name": self.name,
            "resonance": self.resonance,
            "priority": self.priority,
            "timestamp": self.timestamp,
            "data": self.data,
        }
        return payload

    @classmethod
    def from_dict(cls, payload: MutableMapping[str, Any]) -> "PulseEntry":
        name = str(payload.get("name", ""))
        if not name:
            raise ValueError("Pulse entry requires a non-empty 'name'")
        data_field = payload.get("data")
        data: Dict[str, Any]
        if isinstance(data_field, dict):
            data = dict(data_field)
        else:
            data = {}
        return cls(
            name=name,
            resonance=str(payload.get("resonance", "Echo")),
            priority=str(payload.get("priority", "medium")),
            timestamp=str(payload.get("timestamp", _utc_timestamp())),
            data=data,
        )


@dataclass(slots=True)
class PulseLedgerState:
    """In-memory representation of the ledger JSON file."""

    anchor: str = DEFAULT_ANCHOR
    history: List[PulseEntry] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anchor": self.anchor,
            "history": [entry.to_dict() for entry in self.history],
        }

    @classmethod
    def from_dict(cls, payload: MutableMapping[str, Any]) -> "PulseLedgerState":
        anchor = str(payload.get("anchor", DEFAULT_ANCHOR))
        history_payload = payload.get("history", [])
        history: List[PulseEntry] = []
        if isinstance(history_payload, Iterable):
            for item in history_payload:
                if isinstance(item, MutableMapping):
                    try:
                        history.append(PulseEntry.from_dict(item))
                    except ValueError:
                        # Skip malformed entries while salvaging the rest of the ledger.
                        continue
        return cls(anchor=anchor, history=history)


@dataclass(slots=True)
class PulseSnapshot:
    """Summary of the ledger after the latest mutation."""

    anchor: str
    total_pulses: int
    last_pulse: Optional[PulseEntry]
    synced_at: str = field(default_factory=_utc_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anchor": self.anchor,
            "total_pulses": self.total_pulses,
            "last_pulse": self.last_pulse.to_dict() if self.last_pulse else None,
            "synced_at": self.synced_at,
        }


class PulseLedger:
    """Persistent store for pulse events with ergonomic helpers."""

    def __init__(
        self,
        *,
        anchor: str = DEFAULT_ANCHOR,
        file_path: Path | str = DEFAULT_LEDGER_PATH,
    ) -> None:
        self.anchor = anchor
        self.path = Path(file_path)
        self._state = self._load_state()
        # Always prefer the anchor passed in during construction.
        self._state.anchor = anchor

    # ------------------------------------------------------------------
    # Core behaviour
    # ------------------------------------------------------------------
    def record(
        self,
        pulse_name: str,
        *,
        resonance: str = "Echo",
        priority: str = "medium",
        data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
    ) -> PulseEntry:
        """Append a pulse entry to the ledger and persist it to disk."""

        if not pulse_name:
            raise ValueError("pulse_name must be a non-empty string")

        entry = PulseEntry(
            name=pulse_name,
            resonance=resonance,
            priority=priority,
            timestamp=timestamp or _utc_timestamp(),
            data=dict(data or {}),
        )
        self._state.history.append(entry)
        self._persist()
        return entry

    def snapshot(self) -> PulseSnapshot:
        """Return a summary of the ledger's current state."""

        last = self._state.history[-1] if self._state.history else None
        snapshot = PulseSnapshot(
            anchor=self.anchor,
            total_pulses=len(self._state.history),
            last_pulse=last,
        )
        return snapshot

    @property
    def history(self) -> Tuple[PulseEntry, ...]:
        """Immutable view of the recorded pulses."""

        return tuple(self._state.history)

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load_state(self) -> PulseLedgerState:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return PulseLedgerState(anchor=self.anchor)
        except (json.JSONDecodeError, OSError, TypeError):
            return PulseLedgerState(anchor=self.anchor)

        if isinstance(payload, MutableMapping):
            return PulseLedgerState.from_dict(payload)
        return PulseLedgerState(anchor=self.anchor)

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(self._state.to_dict(), handle, indent=2, ensure_ascii=False)


__all__ = [
    "PulseEntry",
    "PulseLedger",
    "PulseLedgerState",
    "PulseSnapshot",
    "DEFAULT_ANCHOR",
    "DEFAULT_LEDGER_PATH",
]

