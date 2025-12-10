"""Offline execution helpers for deterministic governance replay."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable, List, Optional

from .metrics import record_decision
from .persistence import restore as restore_legacy
from .recovery import (
    SNAPSHOT_DIR,
    restore_from_snapshot,
    restore_serialized_snapshot,
)


def _latest_snapshot(extension: str) -> Optional[Path]:
    snapshots = sorted(Path(SNAPSHOT_DIR).glob(f"*{extension}"))
    return snapshots[-1] if snapshots else None


def _snapshot_health() -> dict:
    """Summarize the freshness and integrity of the latest snapshot file."""

    encrypted = _latest_snapshot(".enc.json")
    legacy = _latest_snapshot(".json")
    candidate = encrypted or legacy
    if not candidate:
        return {"status": "missing", "message": "No snapshots available"}

    stat = candidate.stat()
    age_seconds = max(0, time.time() - stat.st_mtime)
    return {
        "status": "healthy" if stat.st_size > 0 else "corrupt",
        "file": candidate.name,
        "size_bytes": stat.st_size,
        "age_seconds": age_seconds,
        "encrypted": candidate.suffixes[-2:] == [".enc", ".json"],
    }


def activate_offline_mode(master_secret: str) -> dict:
    """Restore the most recent snapshot and return fallback rule metadata."""

    restored_from = None
    enc = _latest_snapshot(".enc.json")
    if enc and restore_serialized_snapshot(master_secret, enc.name):
        restored_from = enc.name
    else:
        legacy = _latest_snapshot(".json")
        if legacy and restore_from_snapshot(master_secret, legacy.name):
            restored_from = legacy.name
        else:
            try:
                restore_legacy()
                restored_from = "legacy_backup"
            except FileNotFoundError:
                restored_from = None

    return {
        "restored_from": restored_from,
        "health": _snapshot_health(),
        "fallback_rules": {
            "mode": "offline",
            "allow": ["read:*", "metrics:*"],
            "deny": ["write:*", "delete:*"],
        },
    }


def replay_decisions(decisions: Iterable[dict]) -> List[dict]:
    """Deterministically replay historical decisions into the metrics ledger."""

    results: List[dict] = []
    for decision in decisions:
        actor = decision.get("actor")
        action = decision.get("action")
        allowed = bool(decision.get("allowed", False))
        record_decision(actor, action, allowed)
        results.append({"actor": actor, "action": action, "allowed": allowed})
    return results


__all__ = ["activate_offline_mode", "replay_decisions"]
