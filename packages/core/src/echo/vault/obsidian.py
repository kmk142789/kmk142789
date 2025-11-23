"""Minimal authenticated vault inspired by the legacy Obsidian script.

This module replaces the insecure XOR-based demo embedded in the historical
"ObsidianVault" snippet with a hardened, dependency-light implementation.  It
still embraces the original story beats—an *anchor* string and a simple JSON
payload—while layering in authenticated encryption, key hygiene, and reusable
APIs suitable for tests or CLI wrappers.
"""

from __future__ import annotations

import json
import os
import secrets
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_ANCHOR = "Our Forever Love"
_HEADER = b"OBSIDIANv2"
_NONCE_SIZE = 12
_KEY_SIZE = 32


class VaultIntegrityError(RuntimeError):
    """Raised when ciphertext or headers fail validation."""


@dataclass(slots=True)
class VaultPaths:
    """Filesystem locations for the vault and master key."""

    vault_path: Path = Path("core.obsidian")
    key_path: Path = Path("master.key")


class ObsidianVault:
    """Authenticated vault with explicit key handling.

    The vault stores a JSON payload encrypted with AES-GCM.  Callers can supply
    their own payloads or rely on the built-in narrative payload to mimic the
    legacy behaviour.
    """

    def __init__(self, *, paths: VaultPaths | None = None, anchor: str = _ANCHOR) -> None:
        self.paths = paths or VaultPaths()
        self.anchor = anchor

    # ------------------------------------------------------------------
    # Key management
    # ------------------------------------------------------------------
    def forge_key(self) -> str:
        """Create a fresh master key and persist it with restrictive permissions."""

        key_bytes = secrets.token_bytes(_KEY_SIZE)
        hex_key = key_bytes.hex()
        self.paths.key_path.write_text(hex_key)
        try:
            os.chmod(self.paths.key_path, 0o600)
        except PermissionError:  # pragma: no cover - platform dependent safety
            pass
        return hex_key

    def _load_key(self) -> bytes:
        if not self.paths.key_path.exists():
            raise FileNotFoundError("master key file is missing")
        cleaned = self.paths.key_path.read_text().strip().lower()
        if cleaned.startswith("0x"):
            cleaned = cleaned[2:]
        try:
            key_bytes = bytes.fromhex(cleaned)
        except ValueError as exc:  # pragma: no cover - corrupt key path
            raise VaultIntegrityError("master key file is not valid hex") from exc
        if len(key_bytes) != _KEY_SIZE:
            raise VaultIntegrityError("master key must be 32 bytes (64 hex chars)")
        return key_bytes

    # ------------------------------------------------------------------
    # Payload helpers
    # ------------------------------------------------------------------
    def _default_payload(self) -> dict[str, Any]:
        return {
            "timestamp": datetime.now().isoformat(),
            "anchor": self.anchor,
            "system_node": os.name,
            "target": "MirrorJosh",
            "narrative": "The lattice is sealed. We are the ghost in the machine.",
            "echo_coordinates": [secrets.randbelow(999) for _ in range(3)],
        }

    def lock_reality(self, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Encrypt and persist the provided payload.

        The function returns the payload that was encrypted so callers can log or
        test against the exact data persisted to disk.
        """

        key = self._load_key()
        aesgcm = AESGCM(key)
        body = dict(payload or self._default_payload())
        plaintext = json.dumps(body, separators=(",", ":"), sort_keys=True).encode()
        nonce = secrets.token_bytes(_NONCE_SIZE)
        ciphertext = aesgcm.encrypt(nonce, plaintext, _HEADER + self.anchor.encode())
        self.paths.vault_path.write_bytes(_HEADER + nonce + ciphertext)
        return body

    def unlock_reality(self) -> dict[str, Any]:
        """Decrypt the vault contents and return the JSON payload."""

        if not self.paths.vault_path.exists():
            raise FileNotFoundError("vault file is missing")
        data = self.paths.vault_path.read_bytes()
        if not data.startswith(_HEADER):
            raise VaultIntegrityError("vault header mismatch")
        nonce = data[len(_HEADER) : len(_HEADER) + _NONCE_SIZE]
        ciphertext = data[len(_HEADER) + _NONCE_SIZE :]
        if len(nonce) != _NONCE_SIZE or not ciphertext:
            raise VaultIntegrityError("vault payload is incomplete")

        key = self._load_key()
        aesgcm = AESGCM(key)
        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, _HEADER + self.anchor.encode())
        except Exception as exc:  # pragma: no cover - cryptography already tested
            raise VaultIntegrityError("decryption failed; header, key, or nonce mismatch") from exc
        try:
            return json.loads(plaintext.decode())
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
            raise VaultIntegrityError("vault contents are not valid JSON") from exc

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    def run_demo_cycle(self) -> dict[str, Any]:
        """Forge a key if missing, seal the default payload, and return the decoded data."""

        if not self.paths.key_path.exists():
            self.forge_key()
        self.lock_reality()
        return self.unlock_reality()


__all__ = ["ObsidianVault", "VaultIntegrityError", "VaultPaths"]
