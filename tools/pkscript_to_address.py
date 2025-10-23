"""Utilities for turning simple Bitcoin scripts into Bitcoin addresses."""

from __future__ import annotations

import argparse
from typing import Iterable

from .script_decoder import DecodedScript, PkScriptError, decode_script


def decode_pkscript(lines: Iterable[str] | str, network: str = "mainnet") -> DecodedScript:
    """Decode ``lines`` using the shared Bitcoin script decoder."""

    return decode_script("bitcoin", lines, network=network)


def pkscript_to_address(lines: Iterable[str] | str, network: str = "mainnet") -> str:
    """Convert a textual script representation to a Bitcoin address."""

    decoded = decode_pkscript(lines, network=network)
    if decoded.address is None:
        raise PkScriptError("decoded script did not contain an address")
    return decoded.address


def _build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        help="file containing the script; omit to read from stdin",
    )
    parser.add_argument(
        "--network",
        default="mainnet",
        choices=("mainnet", "testnet", "regtest"),
        help="Bitcoin network to use when selecting the version byte",
    )
    return parser


def main() -> int:
    parser = _build_cli()
    args = parser.parse_args()

    if args.path:
        with open(args.path, "r", encoding="utf8") as handle:
            lines = handle.readlines()
    else:
        import sys

        lines = sys.stdin.readlines()

    decoded = decode_pkscript(lines, network=args.network)
    if decoded.address is None:
        raise PkScriptError("decoded script did not contain an address")
    print(decoded.address)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation
    raise SystemExit(main())
