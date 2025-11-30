"""Policy enforcement for offline agent governance."""

from __future__ import annotations

import fnmatch

from .anomaly_detector import is_blocked
from .audit_log import log_event
from .governance_state import load_state
from .metrics import record_decision
from .roles import ROLES


def enforce(actor: str, action: str) -> bool:
    """Check whether the provided actor is allowed to perform an action."""

    state = load_state()

    if is_blocked(actor):
        allowed = False
        record_decision(actor, action, allowed)
        log_event(actor, action, {"result": "blocked"})
        return False

    actor_info = state["actors"].get(actor, {})
    roles = actor_info.get("roles", [])

    if "superadmin" in roles:
        allowed = True
        record_decision(actor, action, allowed)
        log_event(actor, action, {"result": "allowed", "reason": "superadmin"})
        return True

    allowed = False
    for role in roles:
        allowed_patterns = ROLES.get(role, {}).get("can", [])
        for pattern in allowed_patterns:
            if fnmatch.fnmatch(action, pattern):
                allowed = True
                break
        if allowed:
            break

    record_decision(actor, action, allowed)
    log_event(actor, action, {"result": "allowed" if allowed else "denied"})
    return allowed


__all__ = ["enforce"]
