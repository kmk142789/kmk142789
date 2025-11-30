"""Governance enforcement hooks for revenue operations."""

from echo_governance_core.policy_engine import enforce
from echo_governance_core.audit_log import log_event


def authorize_billing(actor):
    if not enforce(actor, "billing_access"):
        log_event(actor, "billing_denied")
        raise PermissionError("Not authorized for billing")

    log_event(actor, "billing_access")
    return True
