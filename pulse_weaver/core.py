"""Core dataclasses for Pulse Weaver."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Mapping, MutableMapping, Optional


@dataclass(slots=True)
class WeaveFragment:
    """Single ledger entry captured by the Pulse Weaver."""

    key: str
    status: str
    message: str
    cycle: str
    created_at: datetime
    proof: Optional[str] = None
    echo: Optional[str] = None
    metadata: MutableMapping[str, object] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "key": self.key,
            "status": self.status,
            "message": self.message,
            "cycle": self.cycle,
            "created_at": self.created_at.isoformat(),
        }
        if self.proof is not None:
            payload["proof"] = self.proof
        if self.echo is not None:
            payload["echo"] = self.echo
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(slots=True)
class LinkRecord:
    """Mapping tying ledger fragments to Atlas and Phantom references."""

    key: str
    atlas_node: Optional[str]
    phantom_trace: Optional[str]
    created_at: datetime

    def to_dict(self) -> Dict[str, object]:
        data: Dict[str, object] = {
            "key": self.key,
            "created_at": self.created_at.isoformat(),
        }
        if self.atlas_node is not None:
            data["atlas_node"] = self.atlas_node
        if self.phantom_trace is not None:
            data["phantom_trace"] = self.phantom_trace
        return data


@dataclass(slots=True)
class PulseWeaverSnapshot:
    """Structured snapshot returned by :class:`PulseWeaverService`."""

    schema: str
    cycle: Optional[str]
    summary: Mapping[str, object]
    ledger: List[WeaveFragment]
    links: List[LinkRecord]
    phantom: List[Mapping[str, object]]
    rhyme: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "schema": self.schema,
            "cycle": self.cycle,
            "summary": dict(self.summary),
            "ledger": [fragment.to_dict() for fragment in self.ledger],
            "links": [link.to_dict() for link in self.links],
            "phantom": [dict(item) for item in self.phantom],
            "rhyme": self.rhyme,
        }


@dataclass(slots=True)
class CycleMonument:
    """Chronological breakdown for a specific Pulse Weaver cycle."""

    cycle: str
    total: int
    by_status: Mapping[str, int]
    highlights: List[str]
    first_event: Optional[datetime]
    last_event: Optional[datetime]

    def to_dict(self) -> Dict[str, object]:
        data: Dict[str, object] = {
            "cycle": self.cycle,
            "total": self.total,
            "by_status": dict(self.by_status),
            "highlights": list(self.highlights),
        }
        if self.first_event is not None:
            data["first_event"] = self.first_event.isoformat()
        if self.last_event is not None:
            data["last_event"] = self.last_event.isoformat()
        return data


@dataclass(slots=True)
class PulseWeaverMonolith:
    """Grand, multi-cycle synthesis for the Pulse Weaver ledger."""

    schema: str
    magnitude: int
    cycles: List[str]
    timeline: List[CycleMonument]
    statuses: Mapping[str, int]
    atlas: Mapping[str, int]
    phantom: Mapping[str, int]
    proclamation: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "schema": self.schema,
            "magnitude": self.magnitude,
            "cycles": list(self.cycles),
            "timeline": [entry.to_dict() for entry in self.timeline],
            "statuses": dict(self.statuses),
            "atlas": dict(self.atlas),
            "phantom": dict(self.phantom),
            "proclamation": self.proclamation,
        }
