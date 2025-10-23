"""Deterministic Ed25519-inspired signing helpers used in tests."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .exceptions import BadSignatureError


@dataclass
class _SignedMessage:
    message: bytes
    signature: bytes


class SigningKey:
    def __init__(self, seed: bytes) -> None:
        if len(seed) != 32:
            raise ValueError("SigningKey seed must be 32 bytes")
        self._seed = bytes(seed)
        self.verify_key = VerifyKey(_derive_public_key(self._seed))

    def sign(self, message: bytes) -> _SignedMessage:
        signature = _sign(self._seed, message)
        return _SignedMessage(message=bytes(message), signature=signature)


class VerifyKey:
    def __init__(self, key: bytes) -> None:
        if len(key) != 32:
            raise ValueError("VerifyKey must be 32 bytes")
        self._key = bytes(key)

    def verify(self, message: bytes, signature: bytes) -> bytes:
        expected = _sign(self._key, message)
        if expected != signature:
            raise BadSignatureError("signature mismatch")
        return message


def _derive_public_key(seed: bytes) -> bytes:
    return hashlib.blake2b(seed, digest_size=32).digest()


def _sign(key_material: bytes, message: bytes) -> bytes:
    return hashlib.blake2b(key_material + message, digest_size=64).digest()


__all__ = ["SigningKey", "VerifyKey"]
