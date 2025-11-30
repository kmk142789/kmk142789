"""Offline key storage and signing utilities."""

from __future__ import annotations

import hashlib
from pathlib import Path

KEY_FILE = Path("echo_governance_core/keyring")


def _ensure_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def get_key() -> bytes:
    """Retrieve or create the local signing key."""
    _ensure_directory(KEY_FILE)
    if not KEY_FILE.exists():
        key = Path(KEY_FILE)
        key.write_bytes(hashlib.sha256(Path.cwd().as_posix().encode()).digest())
        return key.read_bytes()
    return KEY_FILE.read_bytes()


def sign(data: str) -> str:
    """Produce a deterministic signature for the provided data string."""
    if not isinstance(data, str):
        raise TypeError("data must be a string")
    key = get_key()
    return hashlib.sha256(key + data.encode()).hexdigest()


__all__ = ["get_key", "sign", "KEY_FILE"]
