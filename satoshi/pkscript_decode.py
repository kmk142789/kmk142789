"""Decode human-readable Bitcoin scripts into puzzle metadata."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Optional

from . import puzzle_dataset
from tools import decode_pkscript

from .show_puzzle_solution import (
    SOLUTIONS_PATH,
    _entry_to_solution,
    _load_solutions,
    _match_entry,
)


def _format_solution(solution: puzzle_dataset.PuzzleSolution) -> str:
    """Render a :class:`PuzzleSolution` summary for terminal output."""

    lines = [
        "Lookup        : matched puzzle entry",
        f"Puzzle bits   : {solution.bits}",
        f"Address       : {solution.address}",
        f"Bounty (BTC)  : {solution.btc_value}",
        f"Public key    : {solution.public_key}",
        f"Private key   : {solution.private_key}",
        f"Solve date    : {solution.solve_date}",
    ]
    return "\n".join(lines)


def _decode_script(script: str) -> decode_pkscript.DecodedScript:
    try:
        return decode_pkscript.decode_p2pkh_script(script, network="mainnet")
    except decode_pkscript.ScriptDecodeError as exc:  # pragma: no cover - defensive guard
        raise ValueError(str(exc)) from exc


def _hash_label(script_type: str) -> str:
    if script_type in {"p2pk", "p2pkh"}:
        return "Hash160"
    if script_type == "p2wpkh":
        return "Witness program"
    return "Witness program"


def main(argv: Optional[Iterable[str]] = None) -> None:
    """Decode a canonical Bitcoin script and optionally match the puzzle entry."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "pkscript",
        help=(
            "Canonical Bitcoin locking script in either newline-delimited ASM form "
            "or hexadecimal notation."
        ),
    )
    parser.add_argument(
        "--lookup",
        action="store_true",
        help="Attempt to locate the decoded fingerprint in puzzle_solutions.json.",
    )
    parser.add_argument(
        "--solutions",
        type=Path,
        default=SOLUTIONS_PATH,
        help="Path to the puzzle solutions dataset (defaults to the repository copy).",
    )

    args = parser.parse_args(argv)

    decoded = _decode_script(args.pkscript)

    print(f"Script type   : {decoded.script_type}")
    if decoded.public_key:
        print(f"Public key    : {decoded.public_key}")
    hash_label = _hash_label(decoded.script_type)
    print(f"{hash_label:<13}: {decoded.pubkey_hash}")
    address_label = "Legacy address" if decoded.script_type in {"p2pk", "p2pkh"} else "Address"
    print(f"{address_label:<13}: {decoded.address}")

    if not args.lookup:
        return

    entries = _load_solutions(args.solutions)
    try:
        entry = _match_entry(
            entries,
            address=decoded.address,
            hash160=decoded.pubkey_hash if decoded.script_type in {"p2pkh", "p2pk"} else None,
        )
    except SystemExit:
        print("Lookup        : no matching puzzle entry found.")
        return

    solution = _entry_to_solution(entry)
    print(_format_solution(solution))


if __name__ == "__main__":  # pragma: no cover - module is exercised via CLI tests
    main()
