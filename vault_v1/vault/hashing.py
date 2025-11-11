from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from blake3 import blake3


DEFAULT_CHUNK_SIZE = 1024 * 1024


def hash_bytes(data: bytes) -> str:
    """Return the hexadecimal BLAKE3 hash for the given bytes."""
    return blake3(data).hexdigest()


def hash_concat(hashes: Iterable[str]) -> str:
    concat = "".join(hashes).encode()
    return hash_bytes(concat)


def compute_merkle_root(leaves: List[str]) -> str:
    if not leaves:
        return hash_bytes(b"")
    level = leaves[:]
    while len(level) > 1:
        next_level: List[str] = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else level[i]
            next_level.append(hash_concat((left, right)))
        level = next_level
    return level[0]


@dataclass
class MerkleProof:
    cid: str
    merkle_root: str
    chunk_hashes: List[str]

    def to_dict(self) -> dict:
        return {
            "cid": self.cid,
            "merkle_root": self.merkle_root,
            "chunk_hashes": self.chunk_hashes,
        }


__all__ = ["hash_bytes", "hash_concat", "compute_merkle_root", "MerkleProof", "DEFAULT_CHUNK_SIZE"]
