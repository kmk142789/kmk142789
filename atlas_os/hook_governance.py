"""Atlas OS offline governance gate for feature execution."""

from echo_governance_core.audit_log import log_event
from echo_governance_core.policy_engine import enforce


def gate_os_feature(actor, feature):
    if not enforce(actor, f"os:{feature}"):
        log_event(actor, f"os_denied:{feature}")
        return False

    log_event(actor, f"os_allowed:{feature}")
    return True
