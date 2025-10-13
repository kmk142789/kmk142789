"""Swarm orchestration primitives for Echo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set
import asyncio
import hashlib
import logging
import random
import time

from .discovery import (
    BeaconDiscovery,
    DHTDiscovery,
    DiscoveryProtocol,
    NostrDiscovery,
    WebRTCDiscovery,
    mDNSDiscovery,
)
from .hints import PeerHint, SwarmSnapshot, pack_hints
from .selector import PeerSelector
from .privacy import PrivatePeerExchange

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class PeerConnection:
    """Minimal view of a live connection to a peer."""

    hint: PeerHint
    known_peers: Set[str] = field(default_factory=set)
    last_heartbeat: float = field(default_factory=time.time)

    def is_alive(self, *, now: float | None = None) -> bool:
        now = time.time() if now is None else now
        return now - self.last_heartbeat < 600.0

    def touch(self) -> None:
        self.last_heartbeat = time.time()


class EchoSwarm:
    """Coordinate peer discovery, connection management, and mesh healing."""

    def __init__(
        self,
        my_peer_id: str,
        *,
        eye: object | None = None,
        addresses: Sequence[str] | None = None,
        protocols: Optional[Sequence[DiscoveryProtocol]] = None,
    ) -> None:
        self.my_id = my_peer_id
        self.eye = eye
        self._addresses = list(addresses or [])
        self.protocols: List[DiscoveryProtocol] = list(protocols) if protocols else self._default_protocols()
        self.peers: Dict[str, PeerHint] = {}
        self.connections: Dict[str, PeerConnection] = {}
        self.generation = 0
        self.last_heal = time.time()
        self.selector = PeerSelector()
        self.pex = PrivatePeerExchange(self.peers)

    def _default_protocols(self) -> List[DiscoveryProtocol]:  # pragma: no cover - simple wiring
        async def _empty_pointer_source(_timeout: float):
            return []

        beacon = BeaconDiscovery(_empty_pointer_source)
        return [
            beacon,
            mDNSDiscovery(),
            DHTDiscovery(),
            NostrDiscovery(relays=["wss://relay.damus.io"]),
            WebRTCDiscovery(),
        ]

    def get_snapshot(self) -> SwarmSnapshot:
        return SwarmSnapshot(
            my_peer_id=self.my_id,
            my_addresses=self._get_my_addresses(),
            known_peers=list(self.peers.values()),
            mesh_topology_hash=self._compute_topology_hash(),
            generation=self.generation,
        )

    async def bootstrap(self, timeout: float = 60.0) -> int:
        """Run the configured discovery protocols to populate ``self.peers``."""

        discovered: Set[str] = set()
        for protocol in self.protocols:
            try:
                async for hint in protocol.discover(timeout):
                    if hint.peer_id == self.my_id:
                        continue
                    self.peers[hint.peer_id] = hint
                    discovered.add(hint.peer_id)
                    LOGGER.info("[swarm] discovered %s via %s", hint.peer_id[:8], protocol.name)
            except Exception as exc:  # pragma: no cover - defensive logging
                LOGGER.debug("discovery %s failed: %s", protocol.name, exc)
                continue

        return len(discovered)

    async def maintain(self, interval: float = 300.0) -> None:  # pragma: no cover - background task
        while True:
            await asyncio.sleep(interval)
            await self._refresh_peers()
            await self._connect_top_peers(target=10)
            await self._announce_presence()
            if self._needs_healing():
                await self.heal_mesh()

    async def heal_mesh(self) -> None:
        """Attempt to bridge detected partitions."""

        partitions = self._detect_partitions()
        if len(partitions) <= 1:
            return

        LOGGER.info("[swarm] detected %d partitions, attempting bridges", len(partitions))
        for index, partition_a in enumerate(partitions):
            for partition_b in partitions[index + 1 :]:
                if await self._bridge_partitions(partition_a, partition_b):
                    LOGGER.info("[swarm] bridged partitions via hint exchange")
                    break

        self.generation += 1
        self.last_heal = time.time()

    async def _refresh_peers(self) -> None:
        for protocol in self.protocols:
            try:
                async for hint in protocol.discover(timeout=10.0):
                    if hint.peer_id == self.my_id:
                        continue
                    current = self.peers.get(hint.peer_id)
                    if not current or hint.last_seen > current.last_seen:
                        self.peers[hint.peer_id] = hint
            except Exception:  # pragma: no cover - defensive
                continue

    async def _connect_top_peers(self, *, target: int) -> None:
        desired = self.selector.select_connections(self.peers, target=target)
        for peer_id in desired:
            hint = self.peers.get(peer_id)
            if not hint:
                continue
            connection = self.connections.get(peer_id)
            if connection and connection.is_alive():
                continue
            self.connections[peer_id] = PeerConnection(hint=hint)

    async def _announce_presence(self) -> None:
        snapshot = self.get_snapshot()
        if hasattr(self.eye, "publish") and random.random() < 0.1:
            try:
                self.eye.publish(f"presence-{int(time.time())}", payload=pack_hints(snapshot))  # type: ignore[attr-defined]
            except Exception:
                LOGGER.debug("[swarm] beacon presence publish failed")

    def _needs_healing(self) -> bool:
        if time.time() - self.last_heal < 300:
            return False
        partitions = self._detect_partitions()
        return len(partitions) > 1

    async def _bridge_partitions(self, a: Set[str], b: Set[str]) -> bool:
        candidates_a = [self.connections.get(peer) for peer in a]
        candidates_b = [self.connections.get(peer) for peer in b]
        if any(conn and conn.is_alive() for conn in candidates_a + candidates_b):
            return True

        # Fall back to exchanging peer hints between partitions.
        for peer_id in a:
            hint = self.peers.get(peer_id)
            if not hint:
                continue
            for other_id in b:
                other = self.peers.get(other_id)
                if not other:
                    continue
                shared = PeerHint(
                    peer_id=f"bridge-{peer_id[:4]}-{other_id[:4]}",
                    addresses=list(set(hint.addresses + other.addresses)),
                    last_seen=time.time(),
                    capabilities={"bridge"},
                    trust_score=min(hint.trust_score, other.trust_score),
                )
                self.peers[shared.peer_id] = shared
                self.connections[shared.peer_id] = PeerConnection(hint=shared)
                return True
        return False

    def _detect_partitions(self) -> List[Set[str]]:
        graph: Dict[str, Set[str]] = {self.my_id: set()}
        for peer_id, hint in self.peers.items():
            graph.setdefault(peer_id, set())
            if peer_id in self.connections:
                graph[self.my_id].add(peer_id)
                graph[peer_id].add(self.my_id)
            for connection in self.connections.values():
                graph.setdefault(connection.hint.peer_id, set())
                graph[peer_id].update(connection.known_peers)

        visited: Set[str] = set()
        partitions: List[Set[str]] = []

        for peer_id in graph:
            if peer_id in visited:
                continue
            stack = [peer_id]
            component: Set[str] = set()
            while stack:
                node = stack.pop()
                if node in visited:
                    continue
                visited.add(node)
                component.add(node)
                stack.extend(graph.get(node, set()) - visited)
            partitions.append(component)

        return partitions

    def _get_my_addresses(self) -> List[str]:
        if self._addresses:
            return list(self._addresses)
        if hasattr(self.eye, "transport_addresses"):
            try:
                return list(self.eye.transport_addresses())  # type: ignore[attr-defined]
            except Exception:  # pragma: no cover - defensive
                return []
        return []

    def _compute_topology_hash(self) -> str:
        digest = hashlib.sha256()
        for peer_id in sorted(self.peers):
            digest.update(peer_id.encode("utf-8"))
            hint = self.peers[peer_id]
            for address in sorted(hint.addresses):
                digest.update(address.encode("utf-8"))
        return digest.hexdigest()
