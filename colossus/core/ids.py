"""Identifier utilities for Colossus.

This module intentionally uses only the Python standard library.  It provides
ULID-compatible identifiers alongside shorter, sortable identifiers that can be
used when sharding artifact generation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Tuple
import hashlib
import os

_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_TIME_LEN = 10
_RANDOM_LEN = 16


@dataclass(frozen=True)
class ParsedULID:
    """Parsed components of a ULID identifier."""

    timestamp_ms: int
    randomness: Tuple[int, ...]

    def to_str(self) -> str:
        return encode_ulid(self.timestamp_ms, self.randomness)


def encode_ulid(timestamp_ms: int, randomness: Iterable[int]) -> str:
    """Encode a ULID string from timestamp milliseconds and randomness bytes."""

    if timestamp_ms < 0:
        raise ValueError("timestamp_ms must be non-negative")

    random_bytes = bytes(randomness)
    if len(random_bytes) != 10:
        raise ValueError("randomness must be 10 bytes long")

    value = (timestamp_ms << 80) | int.from_bytes(random_bytes, "big")
    chars = []
    for _ in range(_TIME_LEN + _RANDOM_LEN):
        value, idx = divmod(value, 32)
        chars.append(_ALPHABET[idx])
    return "".join(reversed(chars))


def decode_ulid(ulid: str) -> ParsedULID:
    """Decode a ULID string into its component parts."""

    if len(ulid) != _TIME_LEN + _RANDOM_LEN:
        raise ValueError("ULID must be 26 characters long")

    value = 0
    for char in ulid:
        try:
            value = (value * 32) + _ALPHABET.index(char)
        except ValueError as exc:  # pragma: no cover - defensive branch
            raise ValueError(f"invalid ULID character: {char!r}") from exc

    timestamp_ms = value >> 80
    randomness = tuple(((value >> shift) & 0xFF) for shift in range(72, -8, -8))
    return ParsedULID(timestamp_ms=timestamp_ms, randomness=randomness)


def ulid_now(seed: bytes | str | None = None) -> str:
    """Create a deterministic ULID for the current instant.

    When ``seed`` is provided the randomness portion of the ULID is derived from
    the seed and the current timestamp, making repeated runs with the same seed
    reproducible.
    """

    now = datetime.now(timezone.utc)
    timestamp_ms = int(now.timestamp() * 1000)
    randomness = _random_bytes(timestamp_ms, seed)
    return encode_ulid(timestamp_ms, randomness)


def short_id(prefix: str, index: int) -> str:
    """Return a short, sortable identifier with an alphabetic prefix."""

    if index < 0:
        raise ValueError("index must be non-negative")
    suffix = f"{index:06x}"
    return f"{prefix}-{suffix}"


def _random_bytes(timestamp_ms: int, seed: bytes | None) -> bytes:
    if seed is None:
        return os.urandom(10)
    if isinstance(seed, str):
        seed_bytes = seed.encode("utf-8")
    else:
        seed_bytes = seed
    digest_source = timestamp_ms.to_bytes(8, "big") + seed_bytes
    digest = hashlib.sha256(digest_source).digest()
    return digest[:10]


__all__ = [
    "ParsedULID",
    "decode_ulid",
    "encode_ulid",
    "short_id",
    "ulid_now",
]
