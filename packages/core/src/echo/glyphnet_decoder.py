"""Decode EchoGlyphNet key blobs into structured metadata.

This module extends the EchoGlyphNet protocol by enriching base64 key
fragments with deterministic metadata and lightweight feature extraction.
It is intentionally self contained so that offline analysis tools and CI
checks can reason about key material without reaching for external
services.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import math
import string
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class GlyphnetKeyFeature:
    """Structured description of a decoded key fragment.

    Attributes
    ----------
    token:
        The normalised base64 token.
    payload:
        Raw bytes obtained after decoding ``token``.
    encoding:
        Identifier for the decoding pathway (currently always ``"base64"``).
    length:
        Length of ``payload`` in bytes.
    fingerprint:
        Hex encoded SHA-256 digest of the payload for reproducibility.
    ascii_ratio:
        Ratio of bytes that are printable ASCII characters, rounded to three
        decimals.
    entropy:
        Shannon entropy of the payload, rounded to three decimals.
    is_text:
        ``True`` when the payload can be decoded as UTF-8 without errors.
    preview:
        Human-friendly preview of the payload.  UTF-8 text is emitted as-is
        while binary data is rendered in hexadecimal.
    tags:
        Lightweight classifications used by EchoGlyphNet orchestration.
    """

    token: str
    payload: bytes
    encoding: str
    length: int
    fingerprint: str
    ascii_ratio: float
    entropy: float
    is_text: bool
    preview: str
    tags: Tuple[str, ...]


class GlyphnetKeyDecoder:
    """Decode base64 key blobs and derive EchoGlyphNet feature maps."""

    def decode_tokens(self, tokens: Sequence[str]) -> List[GlyphnetKeyFeature]:
        normalised = [self._normalise_token(token) for token in tokens]
        return [self._decode_token(token) for token in normalised]

    def decode_blob(self, blob: str) -> List[GlyphnetKeyFeature]:
        tokens = [segment for segment in blob.split() if segment]
        return self.decode_tokens(tokens)

    @staticmethod
    def _normalise_token(token: str) -> str:
        cleaned = "".join(token.split())
        padding_needed = (-len(cleaned)) % 4
        padded = cleaned + ("=" * padding_needed)
        return padded

    def _decode_token(self, token: str) -> GlyphnetKeyFeature:
        payload = self._decode_base64(token)
        ascii_ratio = self._ascii_ratio(payload)
        is_text, preview = self._safe_preview(payload)
        entropy = self._entropy(payload)
        tags = self._classify(payload, ascii_ratio, is_text)
        fingerprint = hashlib.sha256(payload).hexdigest()
        return GlyphnetKeyFeature(
            token=token,
            payload=payload,
            encoding="base64",
            length=len(payload),
            fingerprint=fingerprint,
            ascii_ratio=round(ascii_ratio, 3),
            entropy=round(entropy, 3),
            is_text=is_text,
            preview=preview,
            tags=tuple(tags),
        )

    @staticmethod
    def _decode_base64(token: str) -> bytes:
        try:
            return base64.b64decode(token, validate=True)
        except binascii.Error:  # fall back to non-strict decoding
            try:
                return base64.b64decode(token)
            except Exception as inner:
                raise ValueError(f"invalid base64 token: {token}") from inner

    @staticmethod
    def _ascii_ratio(payload: bytes) -> float:
        if not payload:
            return 1.0
        printable = set(string.printable)
        count = sum(1 for byte in payload if chr(byte) in printable)
        return count / len(payload)

    @staticmethod
    def _safe_preview(payload: bytes) -> Tuple[bool, str]:
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError:
            return False, payload.hex()
        else:
            if text and all(char in string.printable for char in text):
                return True, text
            return False, payload.hex()

    @staticmethod
    def _entropy(payload: bytes) -> float:
        if not payload:
            return 0.0
        frequency = {}
        for byte in payload:
            frequency[byte] = frequency.get(byte, 0) + 1
        length = float(len(payload))
        return -sum((count / length) * math.log2(count / length) for count in frequency.values())

    def _classify(self, payload: bytes, ascii_ratio: float, is_text: bool) -> List[str]:
        tags: List[str] = []
        if is_text and ascii_ratio > 0.85:
            tags.append("lexical-glyph")
        else:
            tags.append("binary-glyph")
        if payload.startswith(b"{") or payload.startswith(b"["):
            tags.append("json-candidate")
        if len(payload) in (16, 24, 32, 48, 64):
            tags.append(f"keysize-{len(payload)}")
        if ascii_ratio < 0.2:
            tags.append("high-entropy")
        if not tags:
            tags.append("unknown")
        return tags

    def build_protocol_report(self, features: Iterable[GlyphnetKeyFeature]) -> dict:
        collection = list(features)
        if not collection:
            return {"count": 0, "lexical": 0, "binary": 0, "avg_entropy": 0.0}

        lexical = sum(1 for feature in collection if "lexical-glyph" in feature.tags)
        binary = sum(1 for feature in collection if "binary-glyph" in feature.tags)
        avg_entropy = sum(feature.entropy for feature in collection) / len(collection)
        return {
            "count": len(collection),
            "lexical": lexical,
            "binary": binary,
            "avg_entropy": round(avg_entropy, 3),
            "fingerprints": [feature.fingerprint for feature in collection],
        }
