"""Snapshot and recovery helpers for governance and vault state."""

from __future__ import annotations

import json
import os
import time
from hashlib import sha256

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


__all__ = ["take_snapshot", "restore_from_snapshot", "SNAPSHOT_DIR"]
