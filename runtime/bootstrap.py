"""Runtime bootstrap sequence with self-healing governance persistence."""

from echo_governance_core.persistence import restore, snapshot


def bootstrap_system():
    try:
        snapshot()
    except Exception:
        restore()
