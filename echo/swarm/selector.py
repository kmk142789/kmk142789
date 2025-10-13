"""Peer selection heuristics."""

from __future__ import annotations

from typing import Dict, List
import math
import time

from .hints import PeerHint


class PeerSelector:
    """Rank peers to maintain a healthy and diverse mesh."""

    def select_connections(self, peers: Dict[str, PeerHint], *, target: int = 10) -> List[str]:
        if target <= 0 or not peers:
            return []
        scored = [
            (self._score_peer(hint, peers), peer_id)
            for peer_id, hint in peers.items()
        ]
        scored.sort(reverse=True)
        return [peer_id for _, peer_id in scored[:target]]

    def _score_peer(self, hint: PeerHint, peers: Dict[str, PeerHint]) -> float:
        now = time.time()
        age = max(0.0, now - hint.last_seen)
        recency = math.exp(-age / 3600.0)
        trust = max(0.0, min(1.0, hint.trust_score))
        diversity = min(1.0, len(hint.capabilities) / 5.0)
        connectivity = self._estimate_connectivity(hint, peers)
        strategic = self._strategic_value(hint, peers)
        return (
            recency * 0.3
            + trust * 0.3
            + diversity * 0.1
            + connectivity * 0.2
            + strategic * 0.1
        )

    def _estimate_connectivity(self, hint: PeerHint, peers: Dict[str, PeerHint]) -> float:
        if not peers:
            return 0.0
        address_overlap = sum(
            1 for other in peers.values() if set(other.addresses) & set(hint.addresses)
        )
        return 1.0 - min(1.0, address_overlap / max(1, len(peers)))

    def _strategic_value(self, hint: PeerHint, peers: Dict[str, PeerHint]) -> float:
        unique_caps = {frozenset(h.capabilities) for h in peers.values()}
        if not unique_caps:
            return 0.0
        # Reward peers that bring in rare capability combinations.
        candidate_caps = frozenset(hint.capabilities)
        rarity = sum(1 for caps in unique_caps if candidate_caps.issuperset(caps))
        return 1.0 / rarity if rarity else 0.0
