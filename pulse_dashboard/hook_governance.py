"""Pulse dashboard governance snapshot helper."""

from echo_governance_core.governance_state import load_state


def get_governance_snapshot():
    state = load_state()
    return {
        "policies": state["policies"],
        "roles": state["roles"],
        "recent_audit": state["audit"][-10:],
    }
