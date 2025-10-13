"""Continuity proof utilities for Echo's recovery flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Sequence
import hashlib

Verifier = Callable[[object, bytes, bytes], bool]


@dataclass(slots=True)
class ContinuityProof:
    """Cryptographic linkage between successive snapshots."""

    prev_hash: str
    snapshot_hash: str
    timestamp: float
    signature: bytes
    witness_signatures: Sequence[bytes] = field(default_factory=tuple)

    def verify(
        self,
        pubkey: object,
        prev_proof: Optional["ContinuityProof"] = None,
        *,
        verifier: Verifier | None = None,
    ) -> bool:
        """Verify ordering and signature correctness for this proof."""

        if prev_proof and prev_proof.snapshot_hash != self.prev_hash:
            return False
        if prev_proof and self.timestamp <= prev_proof.timestamp:
            return False

        message = f"{self.prev_hash}:{self.snapshot_hash}:{self.timestamp}".encode()

        if verifier is not None:
            try:
                return bool(verifier(pubkey, message, self.signature))
            except Exception:
                return False

        verify_callable = getattr(pubkey, "verify", None)
        if callable(verify_callable):
            try:
                verify_callable(self.signature, message)
                return True
            except Exception:
                return False

        # Fall back to a best-effort deterministic check for testing.
        return hashlib.sha256(message).digest() == self.signature

    @property
    def chain_strength(self) -> float:
        """Relative strength based on witness signatures."""

        return 1.0 + len(tuple(self.witness_signatures)) * 0.5


def build_continuity_chain(eye: object) -> List[ContinuityProof]:
    """Return the strongest valid chain reconstructed from *eye* beacons."""

    fetcher = getattr(eye, "fetch_continuity_proofs", None)
    if not callable(fetcher):  # pragma: no cover - defensive guard
        return []

    proofs: List[ContinuityProof] = list(fetcher())
    if not proofs:
        return []

    by_prev: dict[str, List[ContinuityProof]] = {}
    all_hashes = {proof.snapshot_hash for proof in proofs}

    for proof in proofs:
        by_prev.setdefault(proof.prev_hash, []).append(proof)

    starts = [p for p in proofs if p.prev_hash not in all_hashes]
    if not starts:
        starts = proofs[:]

    def best_successor(current: ContinuityProof) -> Optional[ContinuityProof]:
        candidates = by_prev.get(current.snapshot_hash, [])
        valid: List[ContinuityProof] = []
        verifier = getattr(eye, "verify_proof", None)
        pubkey = getattr(eye, "public_key", None)
        if callable(getattr(eye, "get_public_key", None)):
            pubkey = eye.get_public_key()

        for candidate in candidates:
            if verifier:
                try:
                    valid_flag = bool(verifier(candidate, current))
                except Exception:
                    continue
            elif pubkey is not None:
                valid_flag = candidate.verify(pubkey, current)
            else:
                valid_flag = candidate.timestamp > current.timestamp
            if valid_flag:
                valid.append(candidate)

        if not valid:
            return None

        valid.sort(key=lambda item: (item.timestamp, item.chain_strength), reverse=True)
        return valid[0]

    def walk(start: ContinuityProof) -> List[ContinuityProof]:
        chain = [start]
        seen = {start.snapshot_hash}
        current = start
        while True:
            next_proof = best_successor(current)
            if not next_proof or next_proof.snapshot_hash in seen:
                break
            chain.append(next_proof)
            seen.add(next_proof.snapshot_hash)
            current = next_proof
        return chain

    chains = [walk(start) for start in starts]
    if not chains:
        return []

    chains.sort(key=lambda chain: (len(chain), chain[-1].chain_strength if chain else 0.0))
    return chains[-1]
