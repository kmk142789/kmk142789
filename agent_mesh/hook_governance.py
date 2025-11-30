"""Governance enforcement hooks for agent mesh actions."""

from echo_governance_core.policy_engine import enforce
from echo_governance_core.audit_log import log_event


def authorize_agent_action(agent_id, action):
    allowed = enforce(agent_id, action)
    log_event(agent_id, action, {"allowed": allowed})

    if not allowed:
        raise PermissionError(f"Agent '{agent_id}' is not allowed to perform '{action}'")

    return True
