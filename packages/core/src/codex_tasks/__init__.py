"""Task implementations for the Echo Codex command line."""

from __future__ import annotations

from .ledger_add import LedgerAddOptions, run_ledger_add
from .verify_wallets import VerifyWalletsOptions, run_verify_wallets

__all__ = [
    "LedgerAddOptions",
    "VerifyWalletsOptions",
    "run_ledger_add",
    "run_verify_wallets",
]


TASK_HANDLERS = {
    "verify_wallets": run_verify_wallets,
    "ledger_add": run_ledger_add,
}

