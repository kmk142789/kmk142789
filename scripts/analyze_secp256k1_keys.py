#!/usr/bin/env python3
"""Analyze candidate secp256k1 private keys that cluster near the curve order.

This utility reads hexadecimal encodings of candidate private keys and reports
whether each value lies in the valid secp256k1 range, along with useful
metadata that helps humans reason about edge cases close to the curve order.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

SECP256K1_ORDER_HEX = "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141"
SECP256K1_ORDER = int(SECP256K1_ORDER_HEX, 16)


@dataclass(frozen=True)
class KeyReport:
    """Structured information about a single key candidate."""

    hex_value: str
    decimal_value: int
    validity: str
    distance_to_order: str

    def format(self) -> str:
        return (
            f"0x{self.hex_value} | {self.decimal_value} | "
            f"{self.validity} | {self.distance_to_order}"
        )

    @property
    def is_valid(self) -> bool:
        return self.validity.startswith("YES")


def parse_keys(lines: Iterable[str]) -> List[str]:
    """Return a normalized list of hexadecimal strings from raw input lines.

    Empty lines and inline comments (introduced with ``#``) are ignored to make
    the input file easier to maintain.
    """

    keys: List[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        comment_pos = line.find("#")
        if comment_pos != -1:
            line = line[:comment_pos].strip()
        if not line:
            continue
        if any(c not in "0123456789abcdefABCDEF" for c in line):
            raise ValueError(f"Invalid hexadecimal character in line: {raw_line.rstrip()}")
        if len(line) != len(SECP256K1_ORDER_HEX):
            raise ValueError(
                "Unexpected key length for line: "
                f"{raw_line.rstrip()} (expected {len(SECP256K1_ORDER_HEX)} hex digits)"
            )
        keys.append(line.lower())
    return keys


def describe_key(hex_value: str) -> KeyReport:
    """Construct a :class:`KeyReport` for the supplied private key candidate."""

    value = int(hex_value, 16)
    if value <= 0:
        validity = "NO (non-positive)"
        distance = "-"
    elif value >= SECP256K1_ORDER:
        validity = "NO (>= order)"
        distance = str(value - SECP256K1_ORDER)
    else:
        validity = "YES"
        distance = str(SECP256K1_ORDER - value)

    return KeyReport(
        hex_value=hex_value,
        decimal_value=value,
        validity=validity,
        distance_to_order=distance,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        nargs="?",
        default=Path("data/secp256k1_edge_private_keys.txt"),
        type=Path,
        help="Path to a newline-delimited file containing candidate keys.",
    )
    args = parser.parse_args()

    try:
        lines = args.source.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:  # pragma: no cover - defensive guardrail
        raise SystemExit(f"Input file not found: {args.source}") from exc

    keys = parse_keys(lines)

    print("secp256k1 order: 0x" + SECP256K1_ORDER_HEX)
    print("value | decimal | valid | distance_to_order")
    print("-" * 118)

    reports = [describe_key(hex_value) for hex_value in keys]
    for report in reports:
        print(report.format())

    print("-" * 118)
    print(f"Total keys analysed: {len(reports)}")
    print(f"Valid secp256k1 keys: {sum(report.is_valid for report in reports)}")
    print(f"Invalid keys: {sum(not report.is_valid for report in reports)}")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
