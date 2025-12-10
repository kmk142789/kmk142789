"""Snapshot and recovery helpers for governance and vault state."""

from __future__ import annotations

import base64
import gzip
import json
import os
import time
from hashlib import sha256

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from .governance_state import load_state, save_state
from .vault import load_vault, save_vault

SNAPSHOT_DIR = "governance_snapshots"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)


def _checksum(obj: dict) -> str:
    raw = json.dumps(obj, sort_keys=True).encode("utf-8")
    return sha256(raw).hexdigest()


def take_snapshot(master_secret: str) -> str:
    """Persist a snapshot of governance state and vault metadata."""

    state = load_state()
    vault = load_vault(master_secret)

    payload = {
        "state": state,
        "vault": {k: v for k, v in vault.items() if k != "master_secret"},
    }
    csum = _checksum(payload)
    payload["checksum"] = csum

    fname = f"snapshot_{int(time.time())}.json"
    path = os.path.join(SNAPSHOT_DIR, fname)
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2)
    return path


def _derive_key(master_secret: str) -> bytes:
    return sha256(master_secret.encode("utf-8")).digest()


def serialize_snapshot(master_secret: str) -> str:
    """Compress and encrypt governance metadata for offline safekeeping."""

    state = load_state()
    vault = load_vault(master_secret)
    payload = {
        "state": state,
        "vault": {k: v for k, v in vault.items() if k != "master_secret"},
    }

    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    compressed = gzip.compress(raw)

    key = _derive_key(master_secret)
    nonce = get_random_bytes(12)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(compressed)

    blob = {
        "version": 1,
        "nonce": base64.b64encode(nonce).decode(),
        "tag": base64.b64encode(tag).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "checksum": sha256(compressed).hexdigest(),
    }

    fname = f"snapshot_{int(time.time())}.enc.json"
    path = os.path.join(SNAPSHOT_DIR, fname)
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(blob, fp, indent=2)
    return path


def restore_serialized_snapshot(master_secret: str, filename: str) -> bool:
    """Restore a compressed+encrypted snapshot created by :func:`serialize_snapshot`."""

    path = os.path.join(SNAPSHOT_DIR, filename)
    if not os.path.exists(path):
        return False

    with open(path, encoding="utf-8") as fp:
        blob = json.load(fp)

    key = _derive_key(master_secret)
    nonce = base64.b64decode(blob["nonce"])
    tag = base64.b64decode(blob["tag"])
    ciphertext = base64.b64decode(blob["ciphertext"])

    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    compressed = cipher.decrypt_and_verify(ciphertext, tag)

    if sha256(compressed).hexdigest() != blob.get("checksum"):
        return False

    payload = json.loads(gzip.decompress(compressed))
    save_state(payload.get("state", {}))
    vault = load_vault(master_secret)
    vault.update(payload.get("vault", {}))
    save_vault(vault, master_secret)
    return True


def restore_from_snapshot(master_secret: str, filename: str) -> bool:
    """Restore state and vault contents from a named snapshot."""

    path = os.path.join(SNAPSHOT_DIR, filename)
    if not os.path.exists(path):
        return False

    with open(path, encoding="utf-8") as fp:
        payload = json.load(fp)

    checksum = payload.pop("checksum")
    if _checksum(payload) != checksum:
        return False

    save_state(payload["state"])
    vault = load_vault(master_secret)
    vault.update(payload["vault"])
    save_vault(vault, master_secret)
    return True


def restore_last_snapshot(master_secret: str | None = None) -> bool:
    """Restore the most recent snapshot on disk.

    The helper searches ``SNAPSHOT_DIR`` for both plaintext and encrypted
    snapshot files, attempting to restore the newest one first. Missing files
    or validation failures result in a graceful ``False`` return instead of an
    exception so that recovery can be invoked from automated guardrails.
    """

    if not os.path.isdir(SNAPSHOT_DIR):
        return False

    master_secret = master_secret or ""
    snapshots = sorted(
        (
            os.path.join(SNAPSHOT_DIR, name)
            for name in os.listdir(SNAPSHOT_DIR)
            if name.startswith("snapshot_") and name.endswith(".json")
        ),
        key=os.path.getmtime,
        reverse=True,
    )

    for path in snapshots:
        filename = os.path.basename(path)
        if filename.endswith(".enc.json"):
            restored = restore_serialized_snapshot(master_secret, filename)
        else:
            restored = restore_from_snapshot(master_secret, filename)
        if restored:
            return True

    return False


__all__ = ["take_snapshot", "restore_from_snapshot", "restore_serialized_snapshot", "restore_last_snapshot", "SNAPSHOT_DIR"]
