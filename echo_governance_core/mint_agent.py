"""Agent identity minting utilities."""

from __future__ import annotations

from typing import Iterable, List, Optional, Dict, Any

from .governance_state import load_state, save_state


def mint_agent(agent_id: str, roles: Iterable[str], metadata: Optional[Dict[str, Any]] = None) -> None:
    """Create or update an agent identity with assigned roles and optional metadata."""

    state = load_state()
    actor = state.setdefault("actors", {}).setdefault(agent_id, {})
    actor["roles"] = list(roles)
    if metadata is not None:
        actor["metadata"] = metadata
    save_state(state)


__all__ = ["mint_agent"]
