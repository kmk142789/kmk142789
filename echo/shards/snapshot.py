"""Snapshot helpers for serialising Echo shard state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import time

try:  # Optional dependency handling for msgpack
    import msgpack  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    msgpack = None

try:  # Optional dependency handling for zstandard
    import zstandard as zstd  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    zstd = None


@dataclass(slots=True)
class Snapshot:
    """Compact representation of the replicated shard state."""

    version: int
    heads: List[str]
    tip: str
    registry: Dict[str, object]
    deltas_since: Optional[str]
    timestamp: float

    def serialize(self) -> bytes:
        """Serialise the snapshot using MsgPack + Zstandard."""

        if msgpack is None or zstd is None:
            raise RuntimeError("msgpack and zstandard are required for snapshot serialisation")

        data = {
            "v": self.version,
            "h": self.heads,
            "t": self.tip,
            "r": self.registry,
            "d": self.deltas_since,
            "ts": self.timestamp,
        }
        packed = msgpack.packb(data, use_bin_type=True)
        return zstd.ZstdCompressor(level=3).compress(packed)

    @classmethod
    def deserialize(cls, blob: bytes) -> "Snapshot":
        """Rehydrate a :class:`Snapshot` from the compact binary payload."""

        if msgpack is None or zstd is None:
            raise RuntimeError("msgpack and zstandard are required for snapshot deserialisation")

        decompressed = zstd.ZstdDecompressor().decompress(blob)
        unpacked = msgpack.unpackb(decompressed, raw=False)
        return cls(
            version=int(unpacked["v"]),
            heads=list(unpacked["h"]),
            tip=str(unpacked["t"]),
            registry=dict(unpacked["r"]),
            deltas_since=unpacked.get("d"),
            timestamp=float(unpacked.get("ts", time.time())),
        )
