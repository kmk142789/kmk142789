"""Swarm snapshot encoding helpers.

These dataclasses are intentionally lightweight; they provide the core
structures required for peer discovery and mesh reconstruction without
bringing in heavy protocol dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Sequence, Set
import json
import logging
import time

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class PeerHint:
    """Minimal information required to attempt a connection to a peer."""

    peer_id: str
    addresses: List[str]
    last_seen: float
    capabilities: Set[str] = field(default_factory=set)
    trust_score: float = 0.0

    def freshness(self, *, now: float | None = None) -> float:
        """Return a value in ``[0, 1]`` describing how recent the hint is."""

        now = time.time() if now is None else now
        age = max(0.0, now - self.last_seen)
        # 1 hour half-life
        decay = pow(0.5, age / 3600.0)
        return decay


@dataclass(slots=True)
class SwarmSnapshot:
    """Description of the swarm state for embedding inside beacons."""

    my_peer_id: str
    my_addresses: List[str]
    known_peers: List[PeerHint]
    mesh_topology_hash: str
    generation: int

    def top_peers(self, limit: int = 10, *, now: float | None = None) -> List[PeerHint]:
        """Return the top peers prioritising trust and recency."""

        now = time.time() if now is None else now
        scored = sorted(
            self.known_peers,
            key=lambda hint: hint.trust_score * max(hint.freshness(now=now), 1e-6),
            reverse=True,
        )
        return scored[:limit]

    @classmethod
    def from_iterable(
        cls,
        *,
        my_peer_id: str,
        my_addresses: Sequence[str] | None,
        peers: Iterable[PeerHint],
        mesh_topology_hash: str,
        generation: int = 0,
    ) -> "SwarmSnapshot":
        return cls(
            my_peer_id=my_peer_id,
            my_addresses=list(my_addresses or []),
            known_peers=list(peers),
            mesh_topology_hash=mesh_topology_hash,
            generation=generation,
        )


def _ensure_bytes(payload: bytes | bytearray | memoryview) -> bytes:
    if isinstance(payload, bytes):
        return payload
    return bytes(payload)


def _compress(data: bytes) -> bytes:
    try:  # pragma: no cover - optional dependency
        import zstandard as zstd

        compressor = zstd.ZstdCompressor(level=9)
        return compressor.compress(data)
    except Exception:  # pragma: no cover - fall back if zstd missing
        LOGGER.debug("zstandard unavailable; storing swarm hints without compression")
        return data


def _decompress(data: bytes) -> bytes:
    try:  # pragma: no cover - optional dependency
        import zstandard as zstd

        decompressor = zstd.ZstdDecompressor()
        return decompressor.decompress(data)
    except Exception:  # pragma: no cover - fall back if zstd missing
        LOGGER.debug("zstandard unavailable; assuming raw swarm hints")
        return data


def _msgpack_pack(obj: object) -> bytes:
    try:  # pragma: no cover - optional dependency
        import msgpack

        return msgpack.packb(obj, use_bin_type=True)
    except Exception:  # pragma: no cover - deterministic fallback
        LOGGER.debug("msgpack unavailable; using JSON encoding for swarm hints")
        return json.dumps(obj, separators=(",", ":")).encode("utf-8")


def _msgpack_unpack(data: bytes) -> dict:
    try:  # pragma: no cover - optional dependency
        import msgpack

        return msgpack.unpackb(data, raw=False)  # type: ignore[return-value]
    except Exception:  # pragma: no cover - deterministic fallback
        LOGGER.debug("msgpack unavailable; decoding swarm hints as JSON")
        return json.loads(data.decode("utf-8"))


def pack_hints(snapshot: SwarmSnapshot, *, limit: int = 10) -> bytes:
    """Create a compact binary payload representing ``snapshot``.

    The payload intentionally keeps only the most trusted peers to stay
    within typical beacon size limits.
    """

    top_peers = snapshot.top_peers(limit=limit)
    payload = {
        "id": snapshot.my_peer_id,
        "addr": list(snapshot.my_addresses),
        "peers": [
            {
                "id": hint.peer_id,
                "addr": list(hint.addresses),
                "seen": float(hint.last_seen),
                "cap": sorted(hint.capabilities),
                "trust": float(hint.trust_score),
            }
            for hint in top_peers
        ],
        "mesh": snapshot.mesh_topology_hash,
        "gen": int(snapshot.generation),
    }
    packed = _msgpack_pack(payload)
    return _compress(packed)


def unpack_hints(blob: bytes) -> SwarmSnapshot:
    """Inverse of :func:`pack_hints`. Returns a :class:`SwarmSnapshot`."""

    raw = _decompress(_ensure_bytes(blob))
    payload = _msgpack_unpack(raw)

    known_peers = [
        PeerHint(
            peer_id=entry.get("id", ""),
            addresses=list(entry.get("addr", [])),
            last_seen=float(entry.get("seen", 0.0)),
            capabilities=set(entry.get("cap", [])),
            trust_score=float(entry.get("trust", 0.0)),
        )
        for entry in payload.get("peers", [])
        if entry.get("id")
    ]

    return SwarmSnapshot(
        my_peer_id=str(payload.get("id", "")),
        my_addresses=list(payload.get("addr", [])),
        known_peers=known_peers,
        mesh_topology_hash=str(payload.get("mesh", "")),
        generation=int(payload.get("gen", 0)),
    )
