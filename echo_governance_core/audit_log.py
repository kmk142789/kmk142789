"""Immutable offline audit logging."""

from __future__ import annotations

import time
from typing import Any, Dict

from .governance_state import load_state, save_state
from .keyring import sign


def log_event(actor: str, action: str, details: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Record an audit event with a deterministic signature.

    Returns the stored entry for further inspection or testing.
    """
    state = load_state()
    entry = {
        "actor": actor,
        "action": action,
        "details": details or {},
        "timestamp": time.time(),
        "signature": sign(actor + action),
    }
    state["audit"].append(entry)
    save_state(state)
    return entry


__all__ = ["log_event"]
