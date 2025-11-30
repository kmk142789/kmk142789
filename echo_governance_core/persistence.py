"""Snapshot and restore helpers for governance state."""

from __future__ import annotations

import shutil
from pathlib import Path

STATE = Path("echo_governance_state.json")
BACKUP = Path("echo_governance_state.bak")


def snapshot() -> None:
    """Create a backup snapshot of the current state."""
    if not STATE.exists():
        raise FileNotFoundError(f"State file not found: {STATE}")
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(STATE, BACKUP)


def restore() -> None:
    """Restore the state from the backup snapshot."""
    if not BACKUP.exists():
        raise FileNotFoundError(f"Backup file not found: {BACKUP}")
    shutil.copy2(BACKUP, STATE)


__all__ = ["snapshot", "restore", "STATE", "BACKUP"]
