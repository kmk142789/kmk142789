"""Peer registry backed by a CRDT map."""

from __future__ import annotations

from typing import Iterable, Optional

from ..crdt.lww import LWWMap
from .peer import Peer


class Registry:
    """Maintain peer metadata using a Last-Write-Wins CRDT."""

    def __init__(self, node_id: str, crdt: Optional[LWWMap] = None) -> None:
        self.crdt = crdt or LWWMap(node_id)

    def add(self, peer: Peer) -> None:
        self.crdt.set(peer.id, {"url": peer.url, "pubkey": peer.pubkey})

    def list(self) -> Iterable[Peer]:
        peers: list[Peer] = []
        for key, value in self.crdt.snapshot().items():
            if ":" in key:
                continue
            if not isinstance(value, dict):
                continue
            url = value.get("url")
            pubkey = value.get("pubkey")
            if url and pubkey:
                peers.append(Peer(id=key, url=url, pubkey=pubkey))
        return peers

    def note_tip(self, peer_id: str, tip: str) -> None:
        self.crdt.set(f"{peer_id}:tip", tip)

    def mark_dead(self, peer_id: str) -> None:
        self.crdt.set(f"{peer_id}:dead", True)

    def merge(self, other: "Registry | LWWMap") -> None:
        if isinstance(other, Registry):
            self.crdt.merge(other.crdt)
        elif isinstance(other, LWWMap):
            self.crdt.merge(other)
        else:
            raise TypeError("Registry.merge expects a Registry or LWWMap instance")

    def snapshot(self) -> dict[str, object]:
        return self.crdt.snapshot()


__all__ = ["Registry"]
