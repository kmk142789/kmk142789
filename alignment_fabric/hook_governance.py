"""Alignment fabric governance signing hooks."""

from echo_governance_core.keyring import sign
from echo_governance_core.audit_log import log_event


def signed_alignment_update(actor, update):
    signature = sign(update)

    log_event(
        actor,
        "alignment_update",
        {
            "update": update,
            "sig": signature,
        },
    )

    return {
        "update": update,
        "signature": signature,
    }
