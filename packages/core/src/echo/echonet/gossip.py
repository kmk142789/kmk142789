"""Lightweight gossip propagation for EchoNet."""

from __future__ import annotations

import hashlib
import json
import random
import urllib.parse
from http.client import HTTPConnection, HTTPSConnection
from typing import Any, Optional

from .peer import Peer

PING = "/api/echonet/ping"
HELLO = "/api/echonet/hello"
STATE = "/api/echonet/state"


def _get(url: str, path: str) -> dict[str, Any]:
    """Perform a blocking HTTP GET returning parsed JSON."""

    parsed = urllib.parse.urlparse(url)
    conn_cls = HTTPSConnection if parsed.scheme == "https" else HTTPConnection
    connection = conn_cls(parsed.netloc)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        payload = response.read() or b"{}"
        return json.loads(payload.decode("utf-8"))
    finally:
        connection.close()


class Gossip:
    """Peer-to-peer fanout gossip with basic Proof-of-Continuity checks."""

    def __init__(self, registry, receipts) -> None:
        self.registry = registry
        self.receipts = receipts

    def pulse(self) -> None:
        """Send a gossip pulse to a random sample of peers."""

        peers = list(self.registry.list())
        random.shuffle(peers)
        for peer in peers[:5]:
            try:
                remote = _get(peer.url, PING)
                if remote.get("ok"):
                    self._sync_with(peer)
            except Exception:
                # Any connectivity issue marks the peer as temporarily dead.
                self.registry.mark_dead(peer.id)

    def _sync_with(self, peer: Peer) -> None:
        """Compare tips with a remote peer and note better chains."""

        try:
            remote = _get(peer.url, STATE)
        except Exception:
            self.registry.mark_dead(peer.id)
            return

        remote_tip = remote.get("tip")
        if not remote_tip:
            return

        remote_merkle = remote.get("merkle")
        if self._better(remote_tip, remote_merkle):
            self.registry.note_tip(peer.id, remote_tip)

    def _better(self, remote_tip: str, remote_merkle: Optional[str] = None) -> bool:
        """Return True when the remote tip should be preferred locally."""

        if not remote_tip:
            return False

        local_tip = self.receipts.tip()
        if remote_tip == local_tip:
            return False

        remote_height = self._safe_height(remote_tip)
        local_height = self._safe_height(local_tip)

        if remote_height > local_height:
            return True
        if remote_height < local_height:
            return False

        if remote_merkle is None:
            return False

        local_merkle_getter = getattr(self.receipts, "merkle", None)
        local_merkle = None
        if callable(local_merkle_getter):
            try:
                local_merkle = local_merkle_getter(local_tip)
            except Exception:
                local_merkle = None

        if local_merkle is None:
            return True

        return hashlib.sha256(remote_merkle.encode("utf-8")).hexdigest() > hashlib.sha256(
            str(local_merkle).encode("utf-8")
        ).hexdigest()

    def _safe_height(self, tip: Optional[str]) -> int:
        if not tip:
            return 0
        try:
            return int(self.receipts.height(tip))
        except Exception:
            return 0


__all__ = ["Gossip", "PING", "HELLO", "STATE"]
