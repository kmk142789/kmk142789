"""Encrypted driver layering AES-256-GCM on top of another driver."""

from __future__ import annotations

import os
from typing import Dict, Iterable, Tuple

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from .memory import MemoryFileDriver

HEADER_MAGIC = b"ATEN"
HEADER_VERSION = 1
NONCE_SIZE = 12
SALT_SIZE = 16


class EncryptedFileDriver:
    """Wrap another driver and transparently encrypt payloads."""

    name = "encryptedFS"

    def __init__(
        self,
        wrapped=None,
        key: bytes | None = None,
        *,
        password: str | None = None,
        salt: bytes | None = None,
    ) -> None:
        if key and password:
            raise ValueError("Provide either a raw key or a password, not both")
        self._wrapped = wrapped or MemoryFileDriver()
        self._master_key, self._password_salt = self._initialise_key_material(
            key, password, salt
        )

    # ------------------------------------------------------------------
    def _initialise_key_material(
        self, key: bytes | None, password: str | None, salt: bytes | None
    ) -> Tuple[bytes, bytes | None]:
        if key:
            if len(key) != 32:
                raise ValueError("AES-256 key must be exactly 32 bytes long")
            return bytes(key), None
        if password:
            salt = salt or os.urandom(SALT_SIZE)
            hkdf = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                info=b"atlas/encryptedfs/master",
            )
            return hkdf.derive(password.encode("utf8")), salt
        return AESGCM.generate_key(bit_length=256), None

    def _derive_file_key(self, salt: bytes) -> AESGCM:
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=b"atlas/encryptedfs/file",
        )
        return AESGCM(hkdf.derive(self._master_key))

    def _encode_payload(self, nonce: bytes, salt: bytes, ciphertext: bytes) -> bytes:
        if len(nonce) != NONCE_SIZE:
            raise ValueError("Nonce must be 12 bytes for AESGCM")
        header = bytearray()
        header.extend(HEADER_MAGIC)
        header.append(HEADER_VERSION)
        header.append(len(salt))
        header.append(len(nonce))
        header.extend(salt)
        header.extend(nonce)
        header.extend(ciphertext)
        return bytes(header)

    def _decode_payload(self, raw: bytes) -> Tuple[bytes, bytes, bytes]:
        if len(raw) < 6 or not raw.startswith(HEADER_MAGIC):
            raise ValueError("Invalid encrypted payload header")
        version = raw[4]
        if version != HEADER_VERSION:
            raise ValueError(f"Unsupported encrypted payload version {version}")
        salt_len = raw[5]
        nonce_len = raw[6]
        offset = 7
        salt = raw[offset : offset + salt_len]
        offset += salt_len
        nonce = raw[offset : offset + nonce_len]
        offset += nonce_len
        ciphertext = raw[offset:]
        if len(nonce) != NONCE_SIZE:
            raise ValueError("Invalid nonce length in payload")
        return salt, nonce, ciphertext

    # ------------------------------------------------------------------
    def read(self, path: str) -> bytes:
        raw = self._wrapped.read(path)
        salt, nonce, ciphertext = self._decode_payload(raw)
        aes = self._derive_file_key(salt)
        return aes.decrypt(nonce, ciphertext, HEADER_MAGIC)

    def write(self, path: str, data: bytes) -> None:
        salt = os.urandom(SALT_SIZE)
        nonce = os.urandom(NONCE_SIZE)
        aes = self._derive_file_key(salt)
        ciphertext = aes.encrypt(nonce, data, HEADER_MAGIC)
        payload = self._encode_payload(nonce, salt, ciphertext)
        self._wrapped.write(path, payload)

    def list(self, prefix: str = "") -> Iterable[str]:
        yield from self._wrapped.list(prefix)

    def delete(self, path: str) -> None:
        self._wrapped.delete(path)

    # ------------------------------------------------------------------
    def export_key_material(self) -> Dict[str, bytes | None]:
        return {
            "master_key": self._master_key,
            "password_salt": self._password_salt,
        }

    def rotate_key(
        self,
        *,
        new_key: bytes | None = None,
        new_password: str | None = None,
        salt: bytes | None = None,
    ) -> None:
        """Re-encrypt stored payloads with new key material."""

        # Cache plaintext prior to swapping keys to avoid partial rotation
        snapshots: Dict[str, bytes] = {}
        for path in list(self._wrapped.list()):
            snapshots[path] = self.read(path)

        self._master_key, self._password_salt = self._initialise_key_material(
            new_key, new_password, salt
        )

        for path, payload in snapshots.items():
            self.write(path, payload)


__all__ = ["EncryptedFileDriver"]
