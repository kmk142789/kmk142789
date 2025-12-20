"""Private secret storage for Echo Bridge decoded payloads."""

from __future__ import annotations

import base64
import binascii
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from uuid import uuid4
import hashlib


@dataclass(slots=True)
class SecretRecord:
    """Metadata describing a stored bridge secret."""

    secret_id: str
    sha256: str
    bytes: int
    label: Optional[str] = None


class BridgeSecretStore:
    """Persist decoded secrets in a private, local directory."""

    def __init__(self, root: Path) -> None:
        self._root = Path(root)
        self._ensure_root()

    @classmethod
    def from_environment(cls, root: Path | None = None) -> "BridgeSecretStore":
        if root is None:
            env_root = os.getenv("ECHO_BRIDGE_SECRET_DIR")
            root = Path(env_root) if env_root else Path("state/bridge/private")
        return cls(root)

    def store_base64(self, encoded: str, *, label: Optional[str] = None) -> SecretRecord:
        if not isinstance(encoded, str) or not encoded.strip():
            raise ValueError("encoded secret payload must be a non-empty string")
        cleaned = "".join(encoded.split())
        padding = (-len(cleaned)) % 4
        candidate = cleaned + ("=" * padding)
        try:
            payload = base64.b64decode(candidate, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("encoded secret payload is not valid Base64") from exc
        return self.store(payload, label=label)

    def store(self, payload: bytes, *, label: Optional[str] = None) -> SecretRecord:
        if not isinstance(payload, (bytes, bytearray)):
            raise ValueError("payload must be bytes")
        payload_bytes = bytes(payload)
        secret_id = uuid4().hex
        digest = hashlib.sha256(payload_bytes).hexdigest()
        record = SecretRecord(secret_id=secret_id, sha256=digest, bytes=len(payload_bytes), label=label)
        path = self._secret_path(secret_id)
        path.write_bytes(payload_bytes)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        return record

    def _secret_path(self, secret_id: str) -> Path:
        return self._root / f"{secret_id}.bin"

    def _ensure_root(self) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self._root, 0o700)
        except OSError:
            pass
