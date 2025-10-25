"""Convert zero-padded hexadecimal integers into decimal values.

The helper accepts either a file path or standard input containing one
hexadecimal value per line.  Each line may include leading zeros or an ``0x``
prefix.  The CLI normalises the input and prints the corresponding decimal
representation.  Empty lines are ignored, allowing callers to feed formatted
blocks directly (such as the user-provided sequence of values ending in
``e2`` through ``10e``).
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List


def _normalise_hex(token: str) -> str:
    """Return a lowercase hexadecimal string without a prefix."""

    stripped = token.strip().lower()
    if stripped.startswith("0x"):
        stripped = stripped[2:]
    return stripped


def hex_to_decimal(lines: Iterable[str]) -> List[int]:
    """Convert an iterable of hexadecimal strings to decimal integers."""

    decimals: List[int] = []
    for index, raw_line in enumerate(lines, start=1):
        token = _normalise_hex(raw_line)
        if not token:
            continue

        try:
            decimals.append(int(token, 16))
        except ValueError as exc:  # pragma: no cover - defensive path
            raise ValueError(
                f"Line {index} is not valid hexadecimal: {raw_line.rstrip()}"
            ) from exc

    return decimals


def main() -> None:
    """Command-line interface for the converter."""

    parser = argparse.ArgumentParser(
        description="Convert hexadecimal integers (one per line) into decimal values.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        help="Optional path to a file.  Reads from stdin when omitted.",
    )

    args = parser.parse_args()

    if args.path:
        lines = args.path.read_text().splitlines()
    else:
        import sys

        lines = sys.stdin.read().splitlines()

    decimals = hex_to_decimal(lines)
    for number in decimals:
        print(number)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
