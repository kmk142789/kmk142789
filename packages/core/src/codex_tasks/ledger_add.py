"""Ledger integration utilities for the Echo Codex wallet verifier."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[4]
LEDGER_DIR = REPO_ROOT / "ledger"
LEDGER_PATH = LEDGER_DIR / "treasury_ledger.json"


@dataclass(slots=True)
class LedgerAddOptions:
    """Options for the ``ledger_add`` task."""

    source_file: Path
    mode: str = "dryrun"


def _load_wallets(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("unexpected ledger source format")
    return data


def _format_initial_balance(wallet: dict[str, object]) -> str:
    balance_eth = wallet.get("balance_eth") or "0"
    balance_usd = wallet.get("balance_usd")
    usd_display = f"${balance_usd:.2f}" if isinstance(balance_usd, (int, float)) else "N/A"
    return f"{balance_eth} ETH (USD {usd_display})"


def _ledger_entry(wallet: dict[str, object], batch_id: str) -> dict[str, object]:
    address = str(wallet.get("address") or "").lower()
    chain = str(wallet.get("chain") or "ethereum")
    signature_hash = wallet.get("signature_hash")
    verified_at = str(wallet.get("time") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    balance_repr = _format_initial_balance(wallet)
    short_addr = address[-8:] if address else "wallet"
    return {
        "id": f"wallet-{short_addr}",
        "type": "rewards",
        "chain": chain,
        "address": wallet.get("address"),
        "verified_by": f"signature:{signature_hash}" if signature_hash else "signature",
        "verified_at": verified_at,
        "initial_balance": balance_repr,
        "allocated_to": "treasury:funding-pipeline-A",
        "status": "active",
        "batch_id": batch_id,
    }


def _verified_wallets(payload: dict[str, object]) -> Iterable[dict[str, object]]:
    wallets = payload.get("wallets")
    if not isinstance(wallets, list):
        return []
    return [item for item in wallets if isinstance(item, dict) and item.get("status") == "VERIFIED"]


def _persist(entries: list[dict[str, object]]) -> None:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    if LEDGER_PATH.exists():
        existing = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        if not isinstance(existing, list):
            existing = []
    else:
        existing = []
    existing.extend(entries)
    LEDGER_PATH.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")


def run_ledger_add(options: LedgerAddOptions) -> dict[str, object]:
    payload = _load_wallets(options.source_file)
    batch_id = str(payload.get("batch_id") or "unknown")
    verified_wallets = list(_verified_wallets(payload))
    entries = [_ledger_entry(wallet, batch_id) for wallet in verified_wallets]

    result = {
        "batch_id": batch_id,
        "source": str(options.source_file),
        "mode": options.mode,
        "entries": entries,
        "verified_count": len(entries),
    }

    if options.mode == "apply":
        _persist(entries)
        print(f"Ledger updated → {LEDGER_PATH.relative_to(REPO_ROOT)} ({len(entries)} entries)")
    else:
        print(f"Ledger dry-run ({len(entries)} entries)")
        for entry in entries:
            print(json.dumps(entry, indent=2))

    return result


__all__ = ["LedgerAddOptions", "run_ledger_add"]

