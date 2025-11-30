"""Runtime governance gate for task execution."""

from echo_governance_core.policy_engine import enforce
from echo_governance_core.audit_log import log_event


def governance_checked_run(actor, task):
    if not enforce(actor, f"run:{task.type}"):
        log_event(actor, f"run_denied:{task.type}", {"task": task.id})
        return "DENIED"

    log_event(actor, f"run:{task.type}", {"task": task.id})
    return "ALLOWED"
