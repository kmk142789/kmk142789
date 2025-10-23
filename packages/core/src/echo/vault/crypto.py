"""Cryptographic helpers for the Echo Vault."""

from __future__ import annotations

import hashlib
import os
from typing import Iterable, Tuple

from nacl import utils
from nacl.exceptions import CryptoError
from nacl.secret import SecretBox

__all__ = [
    "ARGON2_TIME_COST",
    "ARGON2_MEMORY_COST",
    "ARGON2_PARALLELISM",
    "SecretBox",
    "derive_key",
    "encrypt",
    "decrypt",
    "generate_salt",
    "random_nonce",
    "zeroize",
]

SALT_SIZE = 16
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536  # ~64 MiB
ARGON2_PARALLELISM = 2


def generate_salt() -> bytes:
    """Return a new random salt."""

    return utils.random(SALT_SIZE)


def derive_key(
    passphrase: str,
    salt: bytes,
    *,
    time_cost: int = ARGON2_TIME_COST,
    memory_cost: int = ARGON2_MEMORY_COST,
    parallelism: int = ARGON2_PARALLELISM,
) -> bytes:
    """Derive a SecretBox key from ``passphrase``.

    The original project used Argon2id; the simplified kata environment does not
    bundle :mod:`argon2`, so we approximate the behaviour with PBKDF2.  The
    ``time_cost`` parameter controls the iteration count to retain the
    configuration knobs exposed by the public API.
    """

    if not isinstance(passphrase, str):
        raise TypeError("passphrase must be a string")
    if not salt:
        raise ValueError("salt must be non-empty")

    phrase_bytes = bytearray(passphrase.encode("utf-8"))
    try:
        iterations = max(time_cost, 1) * 50_000
        key = hashlib.pbkdf2_hmac(
            "sha256",
            bytes(phrase_bytes),
            salt,
            iterations,
            dklen=SecretBox.KEY_SIZE,
        )
    finally:
        zeroize(phrase_bytes)
    return key


def _box_from_key(key: bytes) -> SecretBox:
    if len(key) != SecretBox.KEY_SIZE:
        raise ValueError("SecretBox keys must be 32 bytes")
    return SecretBox(key)


def random_nonce() -> bytes:
    """Return a fresh random nonce."""

    return os.urandom(SecretBox.NONCE_SIZE)


def encrypt(key: bytes, plaintext: bytes, *, nonce: bytes | None = None) -> Tuple[bytes, bytes]:
    """Encrypt ``plaintext`` returning ``(ciphertext, nonce)``."""

    nonce_to_use = nonce if nonce is not None else random_nonce()
    box = _box_from_key(key)
    ciphertext = box.encrypt(plaintext, nonce_to_use).ciphertext
    return ciphertext, nonce_to_use


def decrypt(key: bytes, ciphertext: bytes, nonce: bytes) -> bytes:
    """Decrypt ``ciphertext`` with the provided ``nonce``."""

    box = _box_from_key(key)
    try:
        return box.decrypt(ciphertext, nonce)
    except CryptoError as exc:
        raise ValueError("failed to decrypt vault record") from exc


def zeroize(buffer: Iterable[int]) -> None:
    """Best-effort memory wipe for mutable buffers."""

    if isinstance(buffer, bytearray):
        for i in range(len(buffer)):
            buffer[i] = 0
    elif isinstance(buffer, memoryview) and not buffer.readonly:
        buffer[:] = b"\x00" * len(buffer)
    elif isinstance(buffer, list):
        for i in range(len(buffer)):
            buffer[i] = 0
