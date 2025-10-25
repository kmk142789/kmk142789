"""Decode human-readable P2PKH scripts into puzzle metadata."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Optional

from . import puzzle_dataset
from .show_puzzle_solution import (
    SOLUTIONS_PATH,
    _decode_script,
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


def main(argv: Optional[Iterable[str]] = None) -> None:
    """Decode a canonical P2PKH script and optionally match the puzzle entry."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "pkscript",
        help=(
            "Canonical P2PKH script in either newline-delimited ASM form or "
            "hexadecimal notation."
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
    if decoded.script_type == "p2pk":
        print("Script type   : pay-to-pubkey")
        if decoded.pubkey:
            print(f"Public key    : {decoded.pubkey}")
        if decoded.pubkey_hash:
            print(f"Hash160       : {decoded.pubkey_hash}")
        print(f"Legacy address: {decoded.address}")
    elif decoded.script_type == "p2wpkh":
        if decoded.pubkey_hash:
            print(f"Witness prog  : {decoded.pubkey_hash}")
        print(f"Bech32 address: {decoded.address}")
    else:
        if decoded.pubkey_hash:
            print(f"Hash160       : {decoded.pubkey_hash}")
        print(f"Legacy address: {decoded.address}")

    if not args.lookup:
        return

    entries = _load_solutions(args.solutions)
    try:
        entry = _match_entry(
            entries,
            hash160=decoded.pubkey_hash,
            address=decoded.address if decoded.script_type in {"p2pkh", "p2pk"} else None,
            pubkey=decoded.pubkey,
        )
    except SystemExit:
        print("Lookup        : no matching puzzle entry found.")
        return

    solution = _entry_to_solution(entry)
    print(_format_solution(solution))


if __name__ == "__main__":  # pragma: no cover - module is exercised via CLI tests
    main()
