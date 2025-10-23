"""Utility for decoding simple pay-to-public-key (P2PK) Bitcoin scripts.

This helper focuses on the classic script pattern ``<pubkey> OP_CHECKSIG``.
Given the hexadecimal representation of the public key, it computes the
associated hash160 and Base58Check (legacy) address, and provides a small
summary that can be used for manual verification when reviewing old P2PK
transactions.
"""

from __future__ import annotations

import argparse
import binascii
import hashlib
from dataclasses import dataclass
from typing import Iterable


MAINNET_PUBKEY_HASH_PREFIX = b"\x00"


@dataclass(frozen=True)
class DecodedP2PK:
    """Decoded representation of a pay-to-public-key script."""

    pubkey_bytes: bytes
    hash160: bytes
    address: str

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-serialisable dictionary."""

        return {
            "pubkey_hex": self.pubkey_bytes.hex(),
            "hash160": self.hash160.hex(),
            "address": self.address,
        }


def base58_encode(data: bytes) -> str:
    """Encode ``data`` using the Bitcoin Base58 alphabet."""

    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    num = int.from_bytes(data, "big")
    encoded = ""

    while num > 0:
        num, rem = divmod(num, 58)
        encoded = alphabet[rem] + encoded

    # Preserve leading zero bytes as "1" characters.
    padding = sum(1 for b in data if b == 0)
    return "1" * padding + encoded


def double_sha256(data: bytes) -> bytes:
    """Compute SHA256(SHA256(data))."""

    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def hash160(data: bytes) -> bytes:
    """Compute RIPEMD160(SHA256(data))."""

    sha = hashlib.sha256(data).digest()
    return hashlib.new("ripemd160", sha).digest()


def checksum_encoded(prefix: bytes, payload: bytes) -> str:
    """Return the Base58Check-encoded string for the given components."""

    raw = prefix + payload
    checksum = double_sha256(raw)[:4]
    return base58_encode(raw + checksum)


def decode_p2pk(pubkey_hex: str, *, prefix: bytes = MAINNET_PUBKEY_HASH_PREFIX) -> DecodedP2PK:
    """Decode a hexadecimal P2PK public key into address details."""

    try:
        pubkey_bytes = binascii.unhexlify(pubkey_hex)
    except (binascii.Error, ValueError) as exc:  # pragma: no cover - defensive branch
        raise ValueError("Public key must be a valid hexadecimal string") from exc

    if len(pubkey_bytes) not in {33, 65}:
        raise ValueError(
            "Public key should be 33 (compressed) or 65 (uncompressed) bytes long",
        )

    h160 = hash160(pubkey_bytes)
    address = checksum_encoded(prefix, h160)
    return DecodedP2PK(pubkey_bytes=pubkey_bytes, hash160=h160, address=address)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pubkey",
        required=True,
        help="Hexadecimal public key from the P2PK script",
    )
    parser.add_argument(
        "--testnet",
        action="store_true",
        help="Decode using the testnet public-key-hash prefix (0x6f).",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    prefix = b"\x6f" if args.testnet else MAINNET_PUBKEY_HASH_PREFIX
    decoded = decode_p2pk(args.pubkey, prefix=prefix)
    for key, value in decoded.to_dict().items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
