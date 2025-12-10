"""Policy enforcement for offline agent governance."""

from __future__ import annotations

import fnmatch

from .anomaly_detector import flag_actor, is_blocked
from .audit_log import log_event
from .governance_state import load_state, save_state
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


def disable_actor(actor: str | None) -> None:
    """Mark an actor as blocked and persist the decision.

    The function is intentionally lightweight so it can be invoked from
    guardrail paths (e.g., rotation policies) without failing. When a valid
    ``actor`` is provided, the actor record is updated with a ``"blocked"``
    flag, a denial decision is recorded for metrics, and the action is
    appended to the audit log. Missing actor IDs are logged as a no-op
    instead of raising to keep rotation workflows resilient.
    """

    if not actor:
        log_event("system", "force_deny", {"result": "noop", "reason": "missing_actor"})
        return

    flag_actor(actor, "blocked")

    state = load_state()
    actor_info = state.setdefault("actors", {}).setdefault(actor, {"roles": [], "flags": []})
    if "blocked" not in actor_info.get("flags", []):
        actor_info.setdefault("flags", []).append("blocked")
    save_state(state)

    record_decision(actor, "force_deny", False)
    log_event(actor, "force_deny", {"result": "blocked"})


__all__ = ["enforce", "disable_actor"]
