"""Utility helpers for reconstructing puzzle addresses from hash160 digests.

The original "Bitcoin puzzle" challenges often reveal the hash160 of the
locking script.  To confirm a published solution we only need to wrap the
hash160 with the mainnet P2PKH version byte (``0x00``) and compute the
Base58Check representation.  This module keeps that logic in one place so the
documentation, proofs, and tests can reference a deterministic implementation
instead of repeating the algorithm inline.
"""

from __future__ import annotations

import argparse
import binascii
import hashlib
from dataclasses import dataclass


BASE58_ALPHABET = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


class PuzzleAddressError(ValueError):
    """Raised when the caller supplies an invalid hash160 payload."""


def _double_sha256(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def _b58encode(data: bytes) -> str:
    """Encode ``data`` into Base58 preserving leading zeroes."""

    zeros = len(data) - len(data.lstrip(b"\x00"))
    value = int.from_bytes(data, "big")
    encoded = bytearray()
    while value:
        value, remainder = divmod(value, 58)
        encoded.append(BASE58_ALPHABET[remainder])
    if not encoded:
        encoded.append(BASE58_ALPHABET[0])
    encoded.extend(b"1" * zeros)
    return bytes(reversed(encoded)).decode("ascii")


@dataclass(slots=True)
class PuzzleAddress:
    """Structured result for a reconstructed puzzle address."""

    hash160: str
    version: int
    address: str

    def to_dict(self) -> dict[str, object]:
        return {"hash160": self.hash160, "version": self.version, "address": self.address}


def hash160_to_p2pkh(hash160_hex: str, version: int = 0x00) -> PuzzleAddress:
    """Return the Base58Check address for the provided hash160 digest."""

    try:
        payload = binascii.unhexlify(hash160_hex)
    except (binascii.Error, ValueError) as exc:
        raise PuzzleAddressError(f"invalid hash160 hex: {hash160_hex}") from exc

    if len(payload) != 20:
        raise PuzzleAddressError(
            f"expected 20-byte hash160, received {len(payload)} bytes from {hash160_hex!r}"
        )

    if not (0 <= version <= 0xFF):
        raise PuzzleAddressError(f"version byte must be between 0 and 255 (got {version})")

    payload_with_version = bytes([version]) + payload
    checksum = _double_sha256(payload_with_version)[:4]
    address = _b58encode(payload_with_version + checksum)
    return PuzzleAddress(hash160=hash160_hex.lower(), version=version, address=address)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Derive P2PKH address from puzzle hash160")
    parser.add_argument("hash160", help="20-byte hash160 in hex form")
    parser.add_argument(
        "--version",
        type=lambda value: int(value, 0),
        default=0x00,
        help="Address version byte (defaults to 0x00 for mainnet P2PKH)",
    )
    parser.add_argument("--json", action="store_true", help="Emit the result as JSON")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    result = hash160_to_p2pkh(args.hash160, version=args.version)
    if args.json:
        import json

        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(result.address)


if __name__ == "__main__":
    main()
