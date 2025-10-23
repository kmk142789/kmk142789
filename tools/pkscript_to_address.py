"""Utilities for turning simple P2PKH scripts into Bitcoin addresses.

This module understands the very common pay-to-public-key-hash (P2PKH)
`pkscript` layout that appears in a lot of wallet export formats:

```
Pkscript
OP_DUP
OP_HASH160
<20 byte hex hash>
OP_EQUALVERIFY
OP_CHECKSIG
```

The helper reads that representation and emits the corresponding base58
address.  The parsing code is intentionally conservative so that we fail
fast on malformed input instead of silently creating the wrong address.
"""

from __future__ import annotations

import argparse
import hashlib
from typing import Iterable


_BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


class PkScriptError(ValueError):
    """Raised when a script does not match the expected P2PKH pattern."""


def _base58check_encode(version: int, payload: bytes) -> str:
    """Return a base58check address for ``payload`` with ``version`` byte."""

    if not 0 <= version <= 0xFF:
        raise ValueError("version must fit inside a single byte")

    data = bytes([version]) + payload
    checksum = hashlib.sha256(hashlib.sha256(data).digest()).digest()[:4]
    return _base58_encode(data + checksum)


def _base58_encode(data: bytes) -> str:
    number = int.from_bytes(data, "big")

    result = ""
    while number > 0:
        number, mod = divmod(number, 58)
        result = _BASE58_ALPHABET[mod] + result

    leading_zeroes = 0
    for byte in data:
        if byte == 0:
            leading_zeroes += 1
        else:
            break

    return "1" * leading_zeroes + result


def _normalise_lines(lines: Iterable[str]) -> list[str]:
    return [line.strip() for line in lines if line.strip()]


def _pkscript_to_hash(lines: Iterable[str]) -> str:
    sequence = _normalise_lines(lines)

    if sequence and sequence[0].lower() == "pkscript":
        sequence = sequence[1:]

    expected = [
        "OP_DUP",
        "OP_HASH160",
        "OP_EQUALVERIFY",
        "OP_CHECKSIG",
    ]

    if len(sequence) != 5:
        raise PkScriptError("expected five components for a P2PKH script")

    if sequence[0:2] != expected[:2] or sequence[3:] != expected[2:]:
        raise PkScriptError("unexpected operations in script")

    hash_candidate = sequence[2]

    if len(hash_candidate) != 40:
        raise PkScriptError("pubkey hash must be 20 bytes of hex")

    try:
        bytes.fromhex(hash_candidate)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise PkScriptError("pubkey hash must be hexadecimal") from exc

    return hash_candidate


def pkscript_to_address(lines: Iterable[str], network: str = "mainnet") -> str:
    """Convert a textual P2PKH script representation to a base58 address."""

    version_map = {"mainnet": 0x00, "testnet": 0x6F, "regtest": 0x6F}

    try:
        version = version_map[network.lower()]
    except KeyError as exc:
        raise ValueError(f"unknown network '{network}'") from exc

    pubkey_hash = _pkscript_to_hash(lines)
    return _base58check_encode(version, bytes.fromhex(pubkey_hash))


def _build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        help="file containing the P2PKH script; omit to read from stdin",
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

    address = pkscript_to_address(lines, args.network)
    print(address)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation
    raise SystemExit(main())

