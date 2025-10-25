#!/usr/bin/env python3
"""Validate secp256k1 private key candidates provided as hexadecimal strings."""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, Tuple


SECP256K1_ORDER_HEX = (
    "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141"
)
SECP256K1_ORDER = int(SECP256K1_ORDER_HEX, 16)


def validate_key(candidate: str) -> Tuple[str, bool, str]:
    """Return a tuple describing whether ``candidate`` is a valid private key.

    The tuple consists of the normalized hexadecimal string, a boolean validity
    flag, and a human-readable message explaining the result.
    """

    normalized = candidate.lower().strip()
    try:
        value = int(normalized, 16)
    except ValueError:
        return normalized, False, "not valid hexadecimal"

    if value == 0:
        return normalized, False, "must be greater than zero"

    if value >= SECP256K1_ORDER:
        return normalized, False, "must be less than the curve order"

    return normalized, True, "valid secp256k1 private key"


def iter_candidates(values: Iterable[str]) -> Iterable[str]:
    for value in values:
        stripped = value.strip()
        if stripped:
            yield stripped


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate whether the provided hexadecimal values are acceptable "
            "secp256k1 private keys (1 <= key < n)."
        )
    )
    parser.add_argument(
        "values",
        nargs="*",
        help="candidate hexadecimal values; if omitted, values are read from stdin",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)
    values = args.values or [line for line in sys.stdin]

    exit_code = 0
    for candidate in iter_candidates(values):
        normalized, is_valid, message = validate_key(candidate)
        print(f"{normalized}\t{message}")
        if not is_valid:
            exit_code = 1

    return exit_code


if __name__ == "__main__":  # pragma: no cover - entrypoint guard
    raise SystemExit(main(sys.argv[1:]))
