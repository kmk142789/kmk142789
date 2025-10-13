"""Common beacon interfaces used by Echo's recovery system."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class BeaconResult:
    """Result returned when publishing payloads to a beacon."""

    id: str
    url: str
    metadata: Mapping[str, Any] | None = None


@runtime_checkable
class Beacon(Protocol):
    """Minimal protocol describing a publish/fetch beacon."""

    name: str

    def publish(self, payload: bytes, tag: str) -> BeaconResult:
        """Publish *payload* to the beacon and return a :class:`BeaconResult`."""

    def fetch(self, reference: str) -> bytes:
        """Fetch raw bytes previously stored at *reference*."""
