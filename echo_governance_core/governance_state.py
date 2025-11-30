"""Local persistent governance state management."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

STATE_FILE = Path("echo_governance_core/state.json")


DEFAULT_STATE: Dict[str, Any] = {
    "policies": {},
    "roles": {},
    "audit": [],
}


def _ensure_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_state() -> Dict[str, Any]:
    """Load the governance state from disk or return defaults.

    Returns a deep copy of the default structure when no state file exists to
    guarantee callers always receive mutable containers.
    """

    if not STATE_FILE.exists():
        return json.loads(json.dumps(DEFAULT_STATE))

    try:
        with STATE_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        # If the state file is unreadable, fall back to defaults to allow
        # continued offline operation.
        return json.loads(json.dumps(DEFAULT_STATE))

    # Ensure required keys exist even if the file is missing them.
    for key, default_value in DEFAULT_STATE.items():
        data.setdefault(key, json.loads(json.dumps(default_value)))

    return data


def save_state(state: Dict[str, Any]) -> None:
    """Persist the provided state to disk safely."""

    _ensure_directory(STATE_FILE)
    temp_file = STATE_FILE.with_suffix(".tmp")
    with temp_file.open("w", encoding="utf-8") as file:
        json.dump(state, file, indent=2)
    temp_file.replace(STATE_FILE)


__all__ = ["load_state", "save_state", "STATE_FILE", "DEFAULT_STATE"]
