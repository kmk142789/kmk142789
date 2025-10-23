"""Simplified symmetric cryptography helper."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from typing import Any

from .exceptions import CryptoError


@dataclass
class _EncryptedMessage:
    ciphertext: bytes


class SecretBox:
    KEY_SIZE = 32
    NONCE_SIZE = 24
    _TAG_SIZE = 16

    def __init__(self, key: bytes) -> None:
        if len(key) != self.KEY_SIZE:
            raise ValueError("SecretBox keys must be 32 bytes")
        self._key = bytes(key)

    def encrypt(self, plaintext: bytes, nonce: bytes) -> _EncryptedMessage:
        if len(nonce) != self.NONCE_SIZE:
            raise ValueError("nonce must be 24 bytes")
        keystream = _derive_keystream(self._key, nonce, len(plaintext))
        cipher = bytes(a ^ b for a, b in zip(plaintext, keystream))
        tag = _auth_tag(self._key, nonce, cipher)
        return _EncryptedMessage(cipher + tag)

    def decrypt(self, ciphertext: bytes, nonce: bytes) -> bytes:
        if len(nonce) != self.NONCE_SIZE:
            raise ValueError("nonce must be 24 bytes")
        if len(ciphertext) < self._TAG_SIZE:
            raise CryptoError("ciphertext truncated")
        cipher, tag = ciphertext[:-self._TAG_SIZE], ciphertext[-self._TAG_SIZE :]
        expected = _auth_tag(self._key, nonce, cipher)
        if not secrets.compare_digest(expected, tag):
            raise CryptoError("authentication failed")
        keystream = _derive_keystream(self._key, nonce, len(cipher))
        return bytes(a ^ b for a, b in zip(cipher, keystream))


def _derive_keystream(key: bytes, nonce: bytes, size: int) -> bytes:
    blocks: list[bytes] = []
    counter = 0
    while sum(len(block) for block in blocks) < size:
        digest = hashlib.blake2b(key + nonce + counter.to_bytes(4, "big"), digest_size=32)
        blocks.append(digest.digest())
        counter += 1
    keystream = b"".join(blocks)
    return keystream[:size]


def _auth_tag(key: bytes, nonce: bytes, cipher: bytes) -> bytes:
    digest = hashlib.blake2b(key + nonce + cipher, digest_size=SecretBox._TAG_SIZE)
    return digest.digest()


__all__ = ["SecretBox"]
