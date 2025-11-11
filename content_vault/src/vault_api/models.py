"""Data models used by the vault API."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Iterable, List, Mapping, Optional


@dataclass
class VaultItem:
    """Represents a stored payload and its metadata."""

    address: str
    content: bytes
    metadata: Mapping[str, str]
    created_at: datetime
    version: int = 1

    def to_dict(self) -> Dict[str, object]:
        return {
            "address": self.address,
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
            "version": self.version,
        }


@dataclass
class ChangeRecord:
    """Tracks how the vault evolved over time."""

    event: str
    reference: str
    timestamp: datetime
    payload: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            "event": self.event,
            "reference": self.reference,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
        }


@dataclass
class IntegrityReport:
    """Summarises the results of an integrity scan."""

    scanned: int
    mismatches: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, object]:
        return {
            "scanned": self.scanned,
            "mismatches": list(self.mismatches),
            "generated_at": self.generated_at.isoformat(),
        }


@dataclass
class QueryResult:
    """Response from a metadata query."""

    hits: Iterable[VaultItem]

    def to_list(self) -> List[Dict[str, object]]:
        return [item.to_dict() for item in self.hits]


@dataclass
class APIError:
    """Container for structured API errors."""

    message: str
    details: Optional[Mapping[str, object]] = None

    def to_dict(self) -> Dict[str, object]:
        payload = {"message": self.message}
        if self.details is not None:
            payload["details"] = dict(self.details)
        return payload
