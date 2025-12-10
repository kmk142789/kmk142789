"""Pulse dashboard governance snapshot helper."""

from echo_governance_core.governance_state import load_state


def get_governance_snapshot():
    state = load_state()
    actors = state.get("actors", {})
    roles = state.get("roles") or {actor: info.get("roles", []) for actor, info in actors.items()}
    policies = state.get("policies", [])
    audit_log = state.get("audit", [])

    return {
        "policies": policies,
        "roles": roles,
        "recent_audit": audit_log[-10:],
    }
