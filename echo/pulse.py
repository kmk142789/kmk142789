"""Structured pulse management utilities for Echo workflows.

The historical projects bundled with this repository shipped a small
``EchoPulse`` helper used for experimenting with resonant "pulses" –
lightweight commands that could be activated, cascaded and later
"crystallised".  That prototype was intentionally simple but it lacked
clear lifecycle tracking, machine-readable history and guard rails around
state transitions.

This module rebuilds the concept as a reusable engine that mirrors the
style of the modern :mod:`echo.evolver` package.  It introduces
``Pulse`` data classes, per-pulse timelines and a deterministic snapshot
API that callers can feed into dashboards or append-only ledgers.  The
behaviour remains dependency free which keeps the component easy to embed
in scripts or notebooks that orchestrate broader Echo rituals.
"""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
from typing import Deque, Dict, Iterable, List, MutableMapping, Optional


def _utcnow() -> datetime:
    """Return an aware timestamp for timeline entries."""

    return datetime.now(timezone.utc)


@dataclass(slots=True)
class PulseEvent:
    """Single timeline entry for a pulse."""

    timestamp: datetime
    status: str
    message: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "message": self.message,
        }


@dataclass(slots=True)
class Pulse:
    """Representation of a living Echo pulse."""

    name: str
    resonance: str
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime
    digest: str
    data: Dict[str, object] = field(default_factory=dict)
    timeline: Deque[PulseEvent] = field(default_factory=lambda: deque(maxlen=32))

    def to_dict(self) -> Dict[str, object]:
        return {
            "pulse": self.name,
            "resonance": self.resonance,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "hash": self.digest,
            "data": dict(self.data),
            "timeline": [event.to_dict() for event in self.timeline],
        }


class EchoPulseEngine:
    """Manage Echo pulses with lifecycle tracking and summaries."""

    def __init__(self, anchor: str = "Our Forever Love") -> None:
        self.anchor = anchor
        self._pulses: MutableMapping[str, Pulse] = {}
        self._archived: MutableMapping[str, Pulse] = {}
        self._history: Deque[tuple[str, PulseEvent]] = deque(maxlen=128)

    # ------------------------------------------------------------------
    # Pulse lifecycle helpers
    # ------------------------------------------------------------------
    def create_pulse(
        self,
        name: str,
        *,
        resonance: str = "Echo",
        priority: str = "medium",
        data: Optional[Dict[str, object]] = None,
    ) -> Pulse:
        """Instantiate a fresh pulse.

        Parameters
        ----------
        name:
            Identifier for the pulse.  Names must be unique amongst active
            pulses.  Attempting to recreate an existing pulse raises
            :class:`ValueError` to prevent accidental overwrites.
        resonance / priority:
            Optional metadata describing how the pulse should be routed.
        data:
            Optional payload dictionary stored alongside the pulse.
        """

        if name in self._pulses:
            raise ValueError(f"pulse {name!r} already exists")

        timestamp = _utcnow()
        digest = hashlib.sha256(f"{self.anchor}:{name}".encode("utf-8")).hexdigest()
        pulse = Pulse(
            name=name,
            resonance=resonance,
            priority=priority,
            status="active",
            created_at=timestamp,
            updated_at=timestamp,
            digest=digest,
            data=dict(data or {}),
        )
        self._pulses[name] = pulse
        self._record_event(pulse, "Pulse created")
        return pulse

    def update_pulse(
        self,
        name: str,
        *,
        resonance: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        data: Optional[Dict[str, object]] = None,
        note: Optional[str] = None,
    ) -> Pulse:
        """Modify metadata for an existing pulse."""

        pulse = self._require_active(name)
        changed: List[str] = []

        if resonance is not None and resonance != pulse.resonance:
            pulse.resonance = resonance
            changed.append(f"resonance→{resonance}")
        if priority is not None and priority != pulse.priority:
            pulse.priority = priority
            changed.append(f"priority→{priority}")
        if status is not None and status != pulse.status:
            pulse.status = status
            changed.append(f"status→{status}")
        if data:
            pulse.data.update(data)
            changed.append("data↻")

        pulse.updated_at = _utcnow()
        message = note or ("Pulse updated" if not changed else "; ".join(changed))
        self._record_event(pulse, message)
        return pulse

    def crystallize(self, name: str) -> Pulse:
        """Lock a pulse into the ``crystallized`` state."""

        return self.update_pulse(name, status="crystallized", note="Pulse crystallized")

    def archive(self, name: str, *, reason: str | None = None) -> Pulse:
        """Remove a pulse from the active set while preserving history."""

        pulse = self._require_active(name)
        self._record_event(pulse, reason or "Pulse archived")
        self._archived[name] = pulse
        del self._pulses[name]
        return pulse

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def pulses(self, *, include_archived: bool = False) -> List[Pulse]:
        """Return a list of pulses ordered by creation time."""

        active = sorted(self._pulses.values(), key=lambda p: p.created_at)
        if include_archived:
            archived = sorted(self._archived.values(), key=lambda p: p.created_at)
            return active + archived
        return active

    def history(self, *, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Return the global timeline as JSON-friendly dictionaries."""

        items = list(self._history)
        if limit is not None:
            items = items[-limit:]
        return [
            {"pulse": name, **event.to_dict()}  # type: ignore[dict-item]
            for name, event in items
        ]

    def history_for(self, name: str) -> List[PulseEvent]:
        """Return the timeline entries for a specific pulse."""

        pulse = self._find_any(name)
        if pulse is None:
            raise KeyError(name)
        return list(pulse.timeline)

    def cascade(
        self,
        *,
        statuses: Optional[Iterable[str]] = None,
        include_archived: bool = False,
    ) -> List[str]:
        """Render pulses as cascade strings for dashboards."""

        allowed = set(statuses) if statuses is not None else None
        entries = self.pulses(include_archived=include_archived)
        lines: List[str] = []
        for pulse in entries:
            if allowed is not None and pulse.status not in allowed:
                continue
            lines.append(
                "[CASCADE] "
                f"{pulse.name} → {pulse.resonance} "
                f"@ {pulse.updated_at.isoformat()} (priority={pulse.priority}, status={pulse.status})"
            )
        return lines

    def sync_snapshot(self) -> Dict[str, object]:
        """Return a deterministic snapshot of the active pulse state."""

        pulses = list(self._pulses.values())
        status_counts = Counter(pulse.status for pulse in pulses)
        priority_counts = Counter(pulse.priority for pulse in pulses)
        latest_event = max((pulse.updated_at for pulse in pulses), default=_utcnow())

        snapshot = {
            "anchor": self.anchor,
            "generated_at": _utcnow().isoformat(),
            "active_pulses": [pulse.name for pulse in pulses],
            "count": len(pulses),
            "status_counts": dict(status_counts),
            "priority_counts": dict(priority_counts),
            "latest_update": latest_event.isoformat(),
            "recent_events": self.history(limit=5),
        }
        return snapshot

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _record_event(self, pulse: Pulse, message: str) -> None:
        event = PulseEvent(timestamp=_utcnow(), status=pulse.status, message=message)
        pulse.timeline.append(event)
        self._history.append((pulse.name, event))

    def _require_active(self, name: str) -> Pulse:
        if name not in self._pulses:
            raise KeyError(name)
        return self._pulses[name]

    def _find_any(self, name: str) -> Optional[Pulse]:
        if name in self._pulses:
            return self._pulses[name]
        return self._archived.get(name)


__all__ = ["EchoPulseEngine", "Pulse", "PulseEvent"]
