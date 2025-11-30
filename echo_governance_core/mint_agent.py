"""Agent identity minting utilities."""

from __future__ import annotations

from typing import Iterable, List

from .governance_state import load_state, save_state


def mint_agent(agent_id: str, roles: Iterable[str]) -> None:
    """Create a new agent identity with assigned roles."""
    state = load_state()
    state.setdefault("actors", {})[agent_id] = {"roles": list(roles)}
    save_state(state)


__all__ = ["mint_agent"]
