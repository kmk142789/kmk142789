"""Hashing helpers for Colossus."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import hashlib


@dataclass(frozen=True)
class HashResult:
    """Result of hashing an artifact."""

    algorithm: str
    hexdigest: str

    def content_address(self) -> str:
        return f"{self.algorithm}:{self.hexdigest}"


def sha256_bytes(data: bytes) -> HashResult:
    digest = hashlib.sha256(data).hexdigest()
    return HashResult("sha256", digest)


def sha1_bytes(data: bytes) -> HashResult:
    digest = hashlib.sha1(data).hexdigest()
    return HashResult("sha1", digest)


def hash_file(path: Path, algorithm: str = "sha256") -> HashResult:
    hasher = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return HashResult(algorithm, hasher.hexdigest())


def merkle_root(digests: Iterable[str]) -> HashResult:
    nodes = [bytes.fromhex(d) for d in digests]
    if not nodes:
        return HashResult("sha256", hashlib.sha256(b"").hexdigest())

    while len(nodes) > 1:
        next_level = []
        for idx in range(0, len(nodes), 2):
            left = nodes[idx]
            right = nodes[idx + 1] if idx + 1 < len(nodes) else left
            combined = hashlib.sha256(left + right).digest()
            next_level.append(combined)
        nodes = next_level
    return HashResult("sha256", nodes[0].hex())


__all__ = [
    "HashResult",
    "hash_file",
    "merkle_root",
    "sha1_bytes",
    "sha256_bytes",
]
