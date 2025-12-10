"""Local persistent governance state management."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

STATE_FILE = Path("echo_governance_state.json")

DEFAULT_STATE: Dict[str, Any] = {
    "actors": {
        "josh.superadmin": {
            "roles": ["superadmin"],
        },
        "system": {
            "roles": ["billing_agent"],
        },
    },
    "domains": {
        "authority": None,
        "managed": [],
    },
    "audit": [],
    "policies": {},
    "roles": {},
}


def _ensure_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _deep_copy(data: Dict[str, Any]) -> Dict[str, Any]:
    return json.loads(json.dumps(data))


def load_state() -> Dict[str, Any]:
    """Load the governance state from disk or return defaults."""

    if not STATE_FILE.exists():
        save_state(DEFAULT_STATE)
        return _deep_copy(DEFAULT_STATE)

    try:
        with STATE_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        save_state(DEFAULT_STATE)
        return _deep_copy(DEFAULT_STATE)

    # Ensure required keys exist
    for key, default_value in DEFAULT_STATE.items():
        data.setdefault(key, _deep_copy(default_value))

    # Merge mandatory actor records without overwriting existing metadata
    actors = data.setdefault("actors", {})
    for actor_id, default_info in DEFAULT_STATE["actors"].items():
        actors.setdefault(actor_id, _deep_copy(default_info))

    # Ensure policy and role maps exist
    data.setdefault("policies", {})
    data.setdefault("roles", {})

    return data


def save_state(state: Dict[str, Any]) -> None:
    """Persist the provided state to disk safely."""

    _ensure_directory(STATE_FILE)
    temp_file = STATE_FILE.with_suffix(".tmp")
    with temp_file.open("w", encoding="utf-8") as file:
        json.dump(state, file, indent=2)
    temp_file.replace(STATE_FILE)


__all__ = ["load_state", "save_state", "STATE_FILE", "DEFAULT_STATE"]
