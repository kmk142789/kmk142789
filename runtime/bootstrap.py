"""Runtime bootstrap sequence with self-healing governance persistence."""

from echo_governance_core.persistence import restore, snapshot
from governance.vault_keeper import run_keeper


def bootstrap_system():
    try:
        snapshot()
    except Exception:
        restore()

    run_keeper()
