"""Auto-assign roles to agents based on their declared type."""

from __future__ import annotations

from .mint_agent import mint_agent

TYPE_ROLE_MAP = {
    "mesh": ["mesh_agent"],
    "runtime": ["agent_runtime"],
    "billing": ["billing_agent"],
    "os": ["os_agent"],
    "alignment": ["alignment_agent"],
}


def auto_register_agent(agent_id: str, agent_type: str) -> None:
    """Register a new agent with roles derived from its type."""

    roles = TYPE_ROLE_MAP.get(agent_type)
    if not roles:
        roles = []
    mint_agent(agent_id, roles)


__all__ = ["auto_register_agent", "TYPE_ROLE_MAP"]
