"""Utility to reconstruct the P2PKH address for Puzzle #256."""
from __future__ import annotations

import argparse
import hashlib

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58encode(payload: bytes) -> str:
    """Encode *payload* using the Bitcoin base58 alphabet.

    The implementation avoids external dependencies so the script can be run in
    minimal environments.
    """

    number = int.from_bytes(payload, "big")
    if number == 0:
        result = ALPHABET[0]
    else:
        encoded = []
        base = len(ALPHABET)
        while number:
            number, remainder = divmod(number, base)
            encoded.append(ALPHABET[remainder])
        result = "".join(reversed(encoded))

    # Preserve each leading zero from the input as a leading "1" in base58.
    pad = 0
    for byte in payload:
        if byte == 0:
            pad += 1
        else:
            break
    return ALPHABET[0] * pad + result


def hash160_to_address(hash160: str, mainnet: bool = True) -> str:
    """Convert a HASH160 fingerprint into a legacy P2PKH address."""

    version = b"\x00" if mainnet else b"\x6f"
    payload = version + bytes.fromhex(hash160)
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    return b58encode(payload + checksum)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hash160", help="20-byte HASH160 fingerprint in hex")
    parser.add_argument(
        "--testnet",
        action="store_true",
        help="Generate a testnet (tb1) address instead of mainnet",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    address = hash160_to_address(args.hash160, mainnet=not args.testnet)
    print(address)


if __name__ == "__main__":
    main()
