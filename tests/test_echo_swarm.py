from __future__ import annotations

import asyncio
import json
import time

from echo.swarm import EchoSwarm, PeerHint, SwarmSnapshot, pack_hints, unpack_hints
from echo.swarm.discovery import DiscoveryProtocol
from echo.swarm.privacy import PrivatePeerExchange


class StubDiscovery(DiscoveryProtocol):
    name = "stub"

    def __init__(self, hints):
        self._hints = hints

    async def discover(self, timeout: float = 30.0):
        for hint in self._hints:
            yield hint
        await asyncio.sleep(0)


def make_hint(peer_id: str, *, trust: float, last_seen: float | None = None) -> PeerHint:
    return PeerHint(
        peer_id=peer_id,
        addresses=[f"{peer_id}.example:9000"],
        last_seen=last_seen or time.time(),
        capabilities={"discovery-opt-in"},
        trust_score=trust,
    )


def test_pack_hints_roundtrip():
    now = time.time()
    peers = [
        make_hint("peer-a", trust=0.9, last_seen=now - 10),
        make_hint("peer-b", trust=0.4, last_seen=now - 20),
        make_hint("peer-c", trust=0.8, last_seen=now - 5),
    ]
    snapshot = SwarmSnapshot.from_iterable(
        my_peer_id="self",
        my_addresses=["0.0.0.0:9999"],
        peers=peers,
        mesh_topology_hash="abc123",
        generation=7,
    )

    blob = pack_hints(snapshot, limit=2)
    restored = unpack_hints(blob)

    assert restored.my_peer_id == "self"
    assert restored.mesh_topology_hash == "abc123"
    assert restored.generation == 7
    assert len(restored.known_peers) == 2
    assert {hint.peer_id for hint in restored.known_peers} <= {"peer-a", "peer-c"}


def test_swarm_bootstrap_collects_peers():
    hints = [
        make_hint("peer-1", trust=0.6),
        make_hint("peer-2", trust=0.7),
    ]
    swarm = EchoSwarm("self", addresses=["self.example:1"], protocols=[StubDiscovery(hints)])
    count = asyncio.run(swarm.bootstrap())
    assert count == 2
    assert set(swarm.peers) == {"peer-1", "peer-2"}


def test_private_peer_exchange_includes_opt_in_peers():
    peers = {
        "peer-1": make_hint("peer-1", trust=0.8),
        "peer-2": make_hint("peer-2", trust=0.2),
    }
    peers["peer-1"].capabilities.add("discovery-opt-in")
    pex = PrivatePeerExchange(peers)

    payload = pex.create_pex_message("peer-x", limit=2)
    decoded = json.loads(payload.decode("utf-8"))

    assert any(entry["peer_id"].startswith("noise-") for entry in decoded)
    assert any(entry["peer_id"] == "peer-1" for entry in decoded)
