"""Utilities for decoding standard Bitcoin P2PKH scripts.

This module focuses on transforming the hash160 contained in a
standard pay-to-public-key-hash (P2PKH) locking script into the
corresponding Base58Check-encoded Bitcoin address.

The canonical script template that is supported looks like this::

    OP_DUP OP_HASH160 <20-byte hash hex> OP_EQUALVERIFY OP_CHECKSIG

Only the mainnet and testnet prefixes are currently implemented.  The
functions raise :class:`ValueError` for malformed scripts so callers can
surface useful error messages to users.
"""

from __future__ import annotations

import argparse
import hashlib
from typing import Iterable


# The Base58 alphabet used for Bitcoin addresses.
_BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _double_sha256(data: bytes) -> bytes:
    """Return the double SHA-256 digest of *data*."""

    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def _base58_encode(data: bytes) -> str:
    """Encode *data* using the Bitcoin Base58 alphabet."""

    leading_zeros = 0
    for byte in data:
        if byte == 0:
            leading_zeros += 1
        else:
            break

    value = int.from_bytes(data, byteorder="big")
    encoded = ""
    while value > 0:
        value, remainder = divmod(value, 58)
        encoded = _BASE58_ALPHABET[remainder] + encoded

    if encoded:
        return "1" * leading_zeros + encoded

    # When all bytes are zero there is no Base58 representation beyond
    # the leading zero markers.  The convention is to emit a single "1".
    return "1" * leading_zeros + ("1" if len(data) else "")


def _hash160_hex_to_address(hash_hex: str, network: str) -> str:
    """Convert a HASH160 hex string to a Bitcoin address for *network*."""

    if len(hash_hex) != 40:
        raise ValueError("HASH160 must be 20 bytes (40 hex characters)")

    try:
        hash_bytes = bytes.fromhex(hash_hex)
    except ValueError as exc:  # pragma: no cover - ValueError provides context
        raise ValueError("HASH160 must be valid hexadecimal") from exc

    if network == "mainnet":
        prefix = b"\x00"
    elif network == "testnet":
        prefix = b"\x6f"
    else:
        raise ValueError("Unsupported network; choose 'mainnet' or 'testnet'")

    payload = prefix + hash_bytes
    checksum = _double_sha256(payload)[:4]
    return _base58_encode(payload + checksum)


def decode_p2pkh_script(script: str, network: str = "mainnet") -> str:
    """Decode a canonical P2PKH locking *script* into a Bitcoin address."""

    tokens = script.strip().split()
    expected = ["OP_DUP", "OP_HASH160", None, "OP_EQUALVERIFY", "OP_CHECKSIG"]
    if len(tokens) != len(expected):
        raise ValueError("Script must contain five tokens")

    for token, template in zip(tokens, expected):
        if template is not None and token.upper() != template:
            raise ValueError("Script does not match P2PKH template")

    hash_hex = tokens[2]
    return _hash160_hex_to_address(hash_hex, network)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Decode a P2PKH script")
    parser.add_argument(
        "script",
        help="Locking script (e.g. 'OP_DUP OP_HASH160 <hash> OP_EQUALVERIFY OP_CHECKSIG')",
    )
    parser.add_argument(
        "--network",
        choices=("mainnet", "testnet"),
        default="mainnet",
        help="Bitcoin network to target (default: mainnet)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    try:
        address = decode_p2pkh_script(args.script, network=args.network)
    except ValueError as exc:
        parser.error(str(exc))

    print(address)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
