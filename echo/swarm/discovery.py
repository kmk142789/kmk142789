"""Discovery protocol abstractions used by :mod:`echo.swarm`."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Awaitable, Callable, Iterable, List, Optional
import asyncio
import json
import logging
import time

from .hints import PeerHint, SwarmSnapshot, unpack_hints

LOGGER = logging.getLogger(__name__)


class DiscoveryProtocol(ABC):
    """Abstract base class for asynchronous peer discovery strategies."""

    name: str = "protocol"

    @abstractmethod
    async def discover(self, timeout: float = 30.0) -> AsyncIterator[PeerHint]:
        """Yield :class:`PeerHint` objects discovered within ``timeout`` seconds."""
        raise NotImplementedError


@dataclass(slots=True)
class BeaconRecord:
    """Representation of a beacon that may contain swarm hints."""

    payload: bytes
    stamp: float


class BeaconDiscovery(DiscoveryProtocol):
    """Recover peer hints embedded inside Echo beacons."""

    name = "beacon"

    def __init__(
        self,
        pointer_source: Callable[[float], Awaitable[Iterable[BeaconRecord]]],
        *,
        snapshot_decoder: Callable[[BeaconRecord], SwarmSnapshot] | None = None,
    ) -> None:
        self._pointer_source = pointer_source
        self._snapshot_decoder = snapshot_decoder or self._decode_record

    async def discover(self, timeout: float = 30.0) -> AsyncIterator[PeerHint]:
        records = await self._pointer_source(timeout)
        for record in records:
            try:
                snapshot = self._snapshot_decoder(record)
            except Exception as exc:  # pragma: no cover - defensive log
                LOGGER.debug("failed to decode swarm snapshot: %s", exc)
                continue

            yield PeerHint(
                peer_id=snapshot.my_peer_id,
                addresses=list(snapshot.my_addresses),
                last_seen=record.stamp,
                capabilities={"beacon"},
                trust_score=0.5,
            )

            for hint in snapshot.known_peers:
                yield hint

    @staticmethod
    def _decode_record(record: BeaconRecord) -> SwarmSnapshot:
        return unpack_hints(record.payload)


class mDNSDiscovery(DiscoveryProtocol):  # pragma: no cover - network heavy
    """Discover local peers using multicast DNS advertisements."""

    name = "mdns"

    async def discover(self, timeout: float = 30.0) -> AsyncIterator[PeerHint]:
        try:
            from zeroconf import ServiceBrowser, Zeroconf, ServiceStateChange  # type: ignore
        except ModuleNotFoundError:
            LOGGER.debug("zeroconf not available; skipping mDNS discovery")
            return

        zeroconf = Zeroconf()
        discovered: List[PeerHint] = []

        def _on_state_change(_zeroconf, service_type, name, state_change):
            if state_change is ServiceStateChange.Added:
                info = zeroconf.get_service_info(service_type, name)
                if not info:
                    return
                peer_id = info.properties.get(b"peer_id") if info.properties else None
                addresses = [f"{addr}:{info.port}" for addr in info.parsed_scoped_addresses()]
                if peer_id:
                    discovered.append(
                        PeerHint(
                            peer_id=peer_id.decode("utf-8"),
                            addresses=addresses,
                            last_seen=time.time(),
                            capabilities={"mdns"},
                            trust_score=0.4,
                        )
                    )

        browser = ServiceBrowser(zeroconf, "_echo._tcp.local.", handlers=[_on_state_change])

        try:
            await asyncio.sleep(timeout)
        finally:
            browser.cancel()
            zeroconf.close()

        for hint in discovered:
            yield hint


class DHTDiscovery(DiscoveryProtocol):  # pragma: no cover - network heavy
    """Mainline DHT lookups for peers announcing in the Echo namespace."""

    name = "dht"

    def __init__(self, namespace: str = "echo") -> None:
        self.namespace = namespace

    async def discover(self, timeout: float = 30.0) -> AsyncIterator[PeerHint]:
        try:
            from pykademlia.client import Client  # type: ignore
        except ModuleNotFoundError:
            LOGGER.debug("pykademlia not available; skipping DHT discovery")
            return

        key = self.namespace.encode("utf-8")
        client = Client()

        try:
            nodes = await asyncio.wait_for(client.get(key), timeout=timeout)
        except Exception:
            nodes = []
        finally:
            await client.close()

        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            peer_id = node.get("peer_id")
            if not peer_id:
                continue
            yield PeerHint(
                peer_id=str(peer_id),
                addresses=list(node.get("addresses", [])),
                last_seen=float(node.get("last_seen", time.time())),
                capabilities=set(node.get("capabilities", ["dht"])),
                trust_score=float(node.get("trust", 0.3)),
            )


class NostrDiscovery(DiscoveryProtocol):  # pragma: no cover - network heavy
    """Query configured Nostr relays for live Echo peers."""

    name = "nostr"

    def __init__(self, relays: Optional[List[str]] = None) -> None:
        self.relays = relays or []

    async def discover(self, timeout: float = 30.0) -> AsyncIterator[PeerHint]:
        try:
            from nostr.relay_manager import RelayManager  # type: ignore
        except ModuleNotFoundError:
            LOGGER.debug("nostr not available; skipping Nostr discovery")
            return

        manager = RelayManager()
        for relay in self.relays:
            manager.add_relay(relay)

        filters = {
            "kinds": [30078],
            "#app": ["echoeye"],
            "#t": ["presence"],
            "since": int(time.time() - 3600),
        }

        try:
            events = await manager.fetch_events_async(filters, timeout=timeout)
        except Exception:
            events = []
        finally:
            manager.close_connections()

        for event in events:
            try:
                content = event.content if hasattr(event, "content") else {}
                if isinstance(content, str):
                    data = json.loads(content)
                else:
                    data = dict(content)
                peer_id = data.get("peer_id")
                if not peer_id:
                    continue
                yield PeerHint(
                    peer_id=str(peer_id),
                    addresses=list(data.get("addresses", [])),
                    last_seen=float(data.get("last_seen", time.time())),
                    capabilities=set(data.get("capabilities", ["nostr"])),
                    trust_score=float(data.get("trust", 0.3)),
                )
            except Exception:  # pragma: no cover - defensive
                continue


class WebRTCDiscovery(DiscoveryProtocol):  # pragma: no cover - placeholder
    """Placeholder for a WebRTC-based peer discovery routine."""

    name = "webrtc"

    async def discover(self, timeout: float = 30.0) -> AsyncIterator[PeerHint]:
        LOGGER.debug("WebRTC discovery not yet implemented")
        return
