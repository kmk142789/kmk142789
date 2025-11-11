"""Compression primitives for Atlas networking."""

from __future__ import annotations

import zlib
from dataclasses import dataclass


@dataclass(slots=True)
class CompressionStats:
    compressed_size: int
    original_size: int

    @property
    def ratio(self) -> float:
        if self.original_size == 0:
            return 1.0
        return self.compressed_size / self.original_size


class Compressor:
    def __init__(self, *, level: int = 6) -> None:
        self._level = level

    def compress(self, payload: bytes) -> tuple[bytes, CompressionStats]:
        compressed = zlib.compress(payload, self._level)
        stats = CompressionStats(len(compressed), len(payload))
        return compressed, stats

    def decompress(self, payload: bytes, *, expected_size: int | None = None) -> bytes:
        data = zlib.decompress(payload)
        if expected_size is not None and len(data) != expected_size:
            raise ValueError("Decompressed payload does not match expected size")
        return data


__all__ = ["Compressor", "CompressionStats"]
