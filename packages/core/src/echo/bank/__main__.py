"""Command-line helpers for operating the Little Footsteps bank stack."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from echo.vault import open_vault
from ledger.little_footsteps_bank import SovereignLedger
from nonprofit_treasury.ledger import TreasuryLedger


DEFAULT_LEDGER_PATH = Path("ledger/little_footsteps_bank.jsonl")
DEFAULT_PUZZLE_PATH = Path("puzzle_solutions/little_footsteps_bank.md")
DEFAULT_PROOFS_DIR = Path("proofs/little_footsteps_bank")
DEFAULT_VAULT_PATH = Path("state/little_footsteps/vault.db")
DEFAULT_TREASURY_LEDGER_PATH = Path("ledger/little_footsteps_treasury.json")
DEFAULT_LINK_PATH = Path("state/little_footsteps/bank_links.json")
DEFAULT_VAULT_PASSPHRASE = "little-footsteps"


def _path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bootstrap and inspect the Little Footsteps sovereign bank.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    start_cmd = subcommands.add_parser(
        "start",
        help="Create the ledger, puzzle log, and proof directory for the bank.",
    )
    start_cmd.add_argument("--bank", default="Little Footsteps Bank", help="Bank label")
    start_cmd.add_argument(
        "--ledger-path",
        type=_path,
        default=DEFAULT_LEDGER_PATH,
        help="Path to the JSONL ledger file",
    )
    start_cmd.add_argument(
        "--puzzle-path",
        type=_path,
        default=DEFAULT_PUZZLE_PATH,
        help="Path to the puzzle documentation file",
    )
    start_cmd.add_argument(
        "--proofs-dir",
        type=_path,
        default=DEFAULT_PROOFS_DIR,
        help="Directory where proof bundles are written",
    )
    start_cmd.add_argument(
        "--vault-path",
        type=_path,
        default=DEFAULT_VAULT_PATH,
        help="Path to the Echo vault database backing the bank",
    )
    start_cmd.add_argument(
        "--vault-passphrase",
        default=DEFAULT_VAULT_PASSPHRASE,
        help="Passphrase used when initialising the vault (ignored if it already exists)",
    )
    start_cmd.add_argument(
        "--treasury-ledger",
        type=_path,
        default=DEFAULT_TREASURY_LEDGER_PATH,
        help="Path to the Nonprofit Treasury JSON ledger",
    )
    start_cmd.add_argument(
        "--link-path",
        type=_path,
        default=DEFAULT_LINK_PATH,
        help="Location for a manifest linking the ledger, vault, and treasury",
    )
    start_cmd.set_defaults(func=_cmd_start)

    return parser


def _cmd_start(args: argparse.Namespace) -> int:
    ledger_path: Path = args.ledger_path
    puzzle_path: Path = args.puzzle_path
    proofs_dir: Path = args.proofs_dir
    vault_path: Path = args.vault_path
    treasury_ledger: Path = args.treasury_ledger
    link_path: Path = args.link_path

    existing: dict[str, bool] = {
        "ledger": ledger_path.exists(),
        "puzzle": puzzle_path.exists(),
        "proofs": proofs_dir.exists(),
        "vault": vault_path.exists(),
        "treasury": treasury_ledger.exists(),
        "link": link_path.exists(),
    }

    # ``SovereignLedger`` bootstraps directories and writes the puzzle header.
    ledger = SovereignLedger(
        bank=args.bank,
        ledger_path=ledger_path,
        puzzle_path=puzzle_path,
        proofs_dir=proofs_dir,
        skip_ots=True,
    )

    ledger.ledger_path.touch(exist_ok=True)

    vault_created, rotation_audit = _ensure_vault(
        vault_path, args.vault_passphrase
    )
    treasury_created = _ensure_treasury_ledger(treasury_ledger)
    link_created = _write_link_manifest(
        link_path,
        bank=args.bank,
        ledger=ledger,
        vault_path=vault_path,
        rotation_audit=rotation_audit,
        treasury_path=treasury_ledger,
    )

    created = _summarize_created(existing, ledger)
    if vault_created:
        created.append(f"vault created at {vault_path}")
    if treasury_created:
        created.append(f"treasury ledger initialised at {treasury_ledger}")
    if link_created:
        created.append(f"link manifest written at {link_path}")
    if created:
        print("Bank scaffolding ready:")
        for line in created:
            print(f"  - {line}")
    else:
        print("Bank scaffolding already initialized — nothing to do.")
    return 0


def _summarize_created(existing: dict[str, bool], ledger: SovereignLedger) -> list[str]:
    created: list[str] = []
    if not existing["ledger"] and ledger.ledger_path.exists():
        created.append(f"ledger created at {ledger.ledger_path}")
    if not existing["puzzle"] and ledger.puzzle_path.exists():
        created.append(f"puzzle log initialized at {ledger.puzzle_path}")
    if not existing["proofs"] and ledger.proofs_dir.exists():
        created.append(f"proof directory created at {ledger.proofs_dir}")
    return created


def _ensure_vault(path: Path, passphrase: str) -> tuple[bool, Path]:
    """Initialise the Echo vault if needed and return creation status."""

    path.parent.mkdir(parents=True, exist_ok=True)
    created = not path.exists()
    vault = open_vault(str(path), passphrase)
    try:
        rotation_audit = vault.rotation_audit_path
    finally:
        vault.close()
    return created, rotation_audit


def _ensure_treasury_ledger(path: Path) -> bool:
    """Ensure a Nonprofit Treasury ledger file exists."""

    path.parent.mkdir(parents=True, exist_ok=True)
    created = False
    if not path.exists():
        path.write_text("[]\n", encoding="utf-8")
        created = True
    # Touch the ledger to validate JSON structure by loading it.
    TreasuryLedger(path)
    return created


def _write_link_manifest(
    destination: Path,
    *,
    bank: str,
    ledger: SovereignLedger,
    vault_path: Path,
    rotation_audit: Path,
    treasury_path: Path,
) -> bool:
    """Persist a manifest connecting the ledger, vault, and treasury artefacts."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    created = not destination.exists()
    payload = {
        "bank": bank,
        "beneficiary": "Little Footsteps",
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ledger": {
            "path": str(ledger.ledger_path),
            "puzzle": str(ledger.puzzle_path),
            "proofs": str(ledger.proofs_dir),
        },
        "vault": {
            "path": str(vault_path),
            "rotation_audit": str(rotation_audit),
        },
        "treasury": {
            "ledger_path": str(treasury_path),
        },
    }
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return created


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
