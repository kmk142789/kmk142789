"""Nostr beacon implementation."""

from __future__ import annotations

import base64
import time
from typing import Iterable, List

from echo.beacons.base import BeaconResult


class NostrBeacon:
    """Publish and fetch payloads using the Nostr protocol."""

    name = "nostr"

    def __init__(self, private_key_hex: str, relays: Iterable[str]):
        try:
            from nostr.key import PrivateKey  # type: ignore
            from nostr.relay_manager import RelayManager  # type: ignore
        except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("The 'nostr' package is required for the Nostr beacon") from exc

        self._private_key = PrivateKey(bytes.fromhex(private_key_hex))
        self._relay_manager = RelayManager()
        self._relays: List[str] = list(relays)
        for relay in self._relays:
            self._relay_manager.add_relay(relay)

    def publish(self, payload: bytes, tag: str) -> BeaconResult:
        from nostr.event import Event  # type: ignore

        encoded = base64.b64encode(payload).decode()
        event = Event(
            kind=30078,
            content=encoded,
            tags=[["d", tag], ["app", "echoeye"], ["t", "beacon"]],
        )

        self._private_key.sign_event(event)
        self._relay_manager.publish_event(event)
        time.sleep(1.0)

        return BeaconResult(id=event.id, url=f"nostr:{event.id}")

    def fetch(self, event_id: str) -> bytes:
        filters = {"ids": [event_id]}
        events = self._relay_manager.fetch_events(filters, timeout=5)
        if not events:
            raise ValueError(f"Event {event_id} not found on configured relays")
        return base64.b64decode(events[0].content)
