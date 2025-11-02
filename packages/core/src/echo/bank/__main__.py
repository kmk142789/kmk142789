"""Command-line helpers for operating the Little Footsteps bank stack."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from ledger.little_footsteps_bank import SovereignLedger


DEFAULT_LEDGER_PATH = Path("ledger/little_footsteps_bank.jsonl")
DEFAULT_PUZZLE_PATH = Path("puzzle_solutions/little_footsteps_bank.md")
DEFAULT_PROOFS_DIR = Path("proofs/little_footsteps_bank")


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
    start_cmd.set_defaults(func=_cmd_start)

    return parser


def _cmd_start(args: argparse.Namespace) -> int:
    ledger_path: Path = args.ledger_path
    puzzle_path: Path = args.puzzle_path
    proofs_dir: Path = args.proofs_dir

    existing: dict[str, bool] = {
        "ledger": ledger_path.exists(),
        "puzzle": puzzle_path.exists(),
        "proofs": proofs_dir.exists(),
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

    created = _summarize_created(existing, ledger)
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


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
