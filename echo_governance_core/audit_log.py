"""Immutable offline audit logging."""

from __future__ import annotations

from typing import Any, Dict

from .governance_state import load_state, save_state


def log_event(actor: str, action: str, meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Record an audit event and persist it to state."""
    state = load_state()
    entry = {
        "actor": actor,
        "action": action,
        "meta": meta or {},
    }
    state["audit"].append(entry)
    save_state(state)
    return entry


__all__ = ["log_event"]
