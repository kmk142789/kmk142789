"""Encrypted vault storage for sensitive governance material."""

from __future__ import annotations

import json
import os
from hashlib import sha256

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

VAULT_FILE = "echo_governance_vault.bin"


def _derive_key(master_secret: str) -> bytes:
    """Derive a symmetric key from the provided master secret."""

    return sha256(master_secret.encode("utf-8")).digest()


def _encrypt(data: bytes, key: bytes) -> bytes:
    """Encrypt data using AES-GCM with a random nonce."""

    nonce = get_random_bytes(12)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return nonce + tag + ciphertext


def _decrypt(blob: bytes, key: bytes) -> bytes:
    """Decrypt AES-GCM data, verifying authenticity."""

    nonce, tag, ciphertext = blob[:12], blob[12:28], blob[28:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)


def load_vault(master_secret: str) -> dict:
    """Load and decrypt the vault contents, returning an empty mapping if missing."""

    if not os.path.exists(VAULT_FILE):
        return {}
    key = _derive_key(master_secret)
    with open(VAULT_FILE, "rb") as fp:
        blob = fp.read()
    raw = _decrypt(blob, key)
    return json.loads(raw.decode("utf-8"))


def save_vault(vault: dict, master_secret: str) -> None:
    """Persist the provided vault mapping using the derived symmetric key."""

    key = _derive_key(master_secret)
    raw = json.dumps(vault, indent=2).encode("utf-8")
    blob = _encrypt(raw, key)
    with open(VAULT_FILE, "wb") as fp:
        fp.write(blob)


def rotate_signing_keys(master_secret: str | None = None) -> dict:
    """Rotate offline signing keys and persist the new version to the vault."""

    master_secret = master_secret or "default"
    vault = load_vault(master_secret)
    keys = vault.setdefault("signing_keys", [])

    new_key = sha256(os.urandom(32)).hexdigest()
    version = len(keys) + 1
    keys.append({"version": version, "key": new_key})

    vault["signing_keys"] = keys
    save_vault(vault, master_secret)
    return {"version": version, "key": new_key}


__all__ = ["load_vault", "save_vault", "rotate_signing_keys", "VAULT_FILE"]
