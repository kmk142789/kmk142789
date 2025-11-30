"""Policy enforcement for offline agent governance."""

from __future__ import annotations

import fnmatch

from .governance_state import load_state
from .roles import ROLES


def enforce(actor: str, action: str) -> bool:
    """Check whether the provided actor is allowed to perform an action."""
    state = load_state()

    roles = state["actors"].get(actor, {}).get("roles", [])

    if "superadmin" in roles:
        return True

    for role in roles:
        allowed_patterns = ROLES.get(role, {}).get("can", [])
        for pattern in allowed_patterns:
            if fnmatch.fnmatch(action, pattern):
                return True

    return False


__all__ = ["enforce"]
