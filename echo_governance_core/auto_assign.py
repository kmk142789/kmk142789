"""Auto-assign roles to agents based on their declared type and live signals."""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from .anomaly_detector import is_blocked
from .governance_state import load_state, save_state
from .mint_agent import mint_agent

TYPE_ROLE_MAP = {
    "mesh": ["mesh_agent"],
    "runtime": ["agent_runtime"],
    "billing": ["billing_agent"],
    "os": ["os_agent"],
    "alignment": ["alignment_agent"],
}

def _compute_trust(agent_id: str) -> float:
    """Compute a simple trust score using historical metrics."""

    state = load_state()
    metrics = state.get("metrics", {}).get("per_actor", {}).get(agent_id, {})
    allowed = metrics.get("allowed", 0)
    denied = metrics.get("denied", 0)
    total = allowed + denied
    if total == 0:
        return 0.5
    base = allowed / total
    if is_blocked(agent_id):
        return base * 0.25
    return base


def _roles_from_usage(usage: Optional[Dict[str, int]]) -> Iterable[str]:
    if not usage:
        return []

    roles: list[str] = []
    events = usage.get("events", 0)
    escalations = usage.get("escalations", 0)

    if events > 1000:
        roles.append("high_load_operator")
    if escalations > 0:
        roles.append("escalation_handler")
    return roles


def auto_register_agent(
    agent_id: str,
    agent_type: str,
    usage_profile: Optional[Dict[str, int]] = None,
    anomaly_flags: Optional[Iterable[str]] = None,
) -> None:
    """Register a new agent with dynamically derived roles.

    The assignment blends static type roles with live trust scores, usage
    profiles, and anomaly signals. Agents with high trust inherit a
    ``trusted_operator`` role, while those with elevated risk receive
    ``quarantined_agent`` to limit their surface area.
    """

    roles = list(TYPE_ROLE_MAP.get(agent_type, []))
    trust = _compute_trust(agent_id)

    if trust >= 0.85:
        roles.append("trusted_operator")
    elif trust < 0.35:
        roles.append("limited_operator")

    roles.extend(_roles_from_usage(usage_profile))

    flags = set(anomaly_flags or [])
    if is_blocked(agent_id) or {"suspicious", "blocked"} & flags:
        roles.append("quarantined_agent")

    unique_roles = list(dict.fromkeys(roles))

    metadata = {
        "agent_type": agent_type,
        "trust_score": round(trust, 3),
        "usage_profile": usage_profile or {},
        "anomaly_flags": sorted(flags),
    }

    mint_agent(agent_id, unique_roles, metadata=metadata)

    state = load_state()
    actor = state.setdefault("actors", {}).setdefault(agent_id, {})
    actor.setdefault("flags", [])
    actor.setdefault("trust_score", metadata["trust_score"])
    actor.setdefault("anomaly_flags", metadata["anomaly_flags"])
    save_state(state)


__all__ = ["auto_register_agent", "TYPE_ROLE_MAP"]
