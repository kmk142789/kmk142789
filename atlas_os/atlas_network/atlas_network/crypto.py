"""Curve25519-based secure channel utilities."""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305


@dataclass
class SecureChannel:
    private_key: x25519.X25519PrivateKey
    public_key: bytes

    @classmethod
    def create(cls) -> "SecureChannel":
        priv = x25519.X25519PrivateKey.generate()
        return cls(priv, priv.public_key().public_bytes_raw())

    def derive(self, peer_public_key: bytes) -> "SessionCipher":
        shared = self.private_key.exchange(x25519.X25519PublicKey.from_public_bytes(peer_public_key))
        return SessionCipher(shared)


class SessionCipher:
    def __init__(self, shared_key: bytes) -> None:
        self._key = ChaCha20Poly1305(shared_key[:32])

    def encrypt(self, plaintext: bytes, *, aad: bytes | None = None) -> bytes:
        nonce = secrets.token_bytes(12)
        return nonce + self._key.encrypt(nonce, plaintext, aad)

    def decrypt(self, ciphertext: bytes, *, aad: bytes | None = None) -> bytes:
        nonce, payload = ciphertext[:12], ciphertext[12:]
        return self._key.decrypt(nonce, payload, aad)


__all__ = ["SecureChannel", "SessionCipher"]
