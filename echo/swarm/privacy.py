"""Privacy-preserving peer exchange helpers."""

from __future__ import annotations

from typing import Dict, Iterable, List
import json
import secrets

from .hints import PeerHint


class PrivatePeerExchange:
    """Share peer hints conservatively to avoid topology leaks."""

    def __init__(self, peers: Dict[str, PeerHint]) -> None:
        self._peers = peers

    def create_pex_message(self, requesting_peer: str, *, limit: int = 8) -> bytes:
        candidates = list(self._eligible_peers(exclude={requesting_peer}))
        noise = self._generate_noise_peers(count=max(0, limit - len(candidates)))
        payload = candidates[:limit] + noise
        data = [self._serialise_hint(hint) for hint in payload]
        return json.dumps(data, separators=(",", ":")).encode("utf-8")

    def _eligible_peers(self, *, exclude: Iterable[str]) -> Iterable[PeerHint]:
        excluded = set(exclude)
        for peer_id, hint in self._peers.items():
            if peer_id in excluded:
                continue
            if not hint.addresses:
                continue
            if any(addr.startswith("192.168.") or addr.startswith("10.") for addr in hint.addresses):
                continue
            if "discovery-opt-in" not in hint.capabilities:
                continue
            if hint.trust_score <= 0.5:
                continue
            yield hint

    def _generate_noise_peers(self, *, count: int) -> List[PeerHint]:
        peers: List[PeerHint] = []
        for _ in range(count):
            peer_id = secrets.token_hex(8)
            peers.append(
                PeerHint(
                    peer_id=f"noise-{peer_id}",
                    addresses=[f"{peer_id}.invalid:0"],
                    last_seen=0.0,
                    capabilities={"noise"},
                    trust_score=0.0,
                )
            )
        return peers

    @staticmethod
    def _serialise_hint(hint: PeerHint) -> dict:
        return {
            "peer_id": hint.peer_id,
            "addresses": hint.addresses,
            "last_seen": hint.last_seen,
            "capabilities": sorted(hint.capabilities),
            "trust": hint.trust_score,
        }
