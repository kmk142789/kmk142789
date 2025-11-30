"""Policy enforcement for offline agent governance."""

from __future__ import annotations

from typing import Iterable, List

from .governance_state import load_state, save_state


def enforce(actor: str, action: str) -> bool:
    """Check whether the provided actor is allowed to perform an action."""
    state = load_state()
    role = state["roles"].get(actor)
    if role is None:
        return False

    allowed_actions: List[str] = state["policies"].get(role, [])
    return action in allowed_actions


def add_policy(role: str, action: str) -> None:
    """Add a single action to a role's allowed policy list."""
    state = load_state()
    actions: List[str] = state["policies"].setdefault(role, [])
    if action not in actions:
        actions.append(action)
        save_state(state)


def add_policies(role: str, actions: Iterable[str]) -> None:
    """Add multiple actions to a role in one operation."""
    state = load_state()
    existing: List[str] = state["policies"].setdefault(role, [])
    updated = False
    for action in actions:
        if action not in existing:
            existing.append(action)
            updated = True
    if updated:
        save_state(state)


__all__ = ["enforce", "add_policy", "add_policies"]
