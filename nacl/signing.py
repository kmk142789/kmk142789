"""Minimal Ed25519-compatible signing primitives backed by ``cryptography``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from .exceptions import BadSignatureError


@dataclass
class _SignedMessage:
    message: bytes
    signature: bytes


class SigningKey:
    """Wrapper around :class:`Ed25519PrivateKey` for deterministic signing."""

    def __init__(self, seed: bytes) -> None:
        if len(seed) != 32:
            raise ValueError("SigningKey seed must be 32 bytes")
        self._seed = bytes(seed)
        self._private_key = Ed25519PrivateKey.from_private_bytes(self._seed)
        self.verify_key = VerifyKey(self._private_key.public_key())

    def sign(self, message: bytes) -> _SignedMessage:
        signature = self._private_key.sign(message)
        return _SignedMessage(message=bytes(message), signature=signature)


class VerifyKey:
    """Lightweight adapter that exposes ``verify`` for Ed25519 signatures."""

    def __init__(self, key: Union[bytes, Ed25519PublicKey]) -> None:
        if isinstance(key, Ed25519PublicKey):
            self._public_key = key
        elif isinstance(key, (bytes, bytearray)):
            material = bytes(key)
            if len(material) != 32:
                raise ValueError("VerifyKey must be 32 bytes")
            self._public_key = Ed25519PublicKey.from_public_bytes(material)
        else:  # pragma: no cover - defensive type check
            raise TypeError("key must be bytes or an Ed25519PublicKey instance")
        self._key = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

    def verify(self, message: bytes, signature: bytes) -> bytes:
        try:
            self._public_key.verify(signature, message)
        except InvalidSignature as exc:
            raise BadSignatureError("signature mismatch") from exc
        return message


__all__ = ["SigningKey", "VerifyKey"]
