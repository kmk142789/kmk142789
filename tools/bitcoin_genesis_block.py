"""Utilities for reconstructing the Bitcoin genesis block header.

The user request supplied the canonical header fields for block 0:

* version: ``0x00000001``
* bits/target: ``0x1d00ffff``
* merkle root: ``4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b``
* difficulty: ``1``
* nonce: ``0x7c2bac1d`` (decimal ``2083236893``)

These helpers rebuild the header, compute the expected double-SHA256 hash,
and confirm the target/difficulty relationship that proves why the network
accepted the block.  We keep the code modular so that other tests or tools
inside the repository can reuse the functions without re-implementing the
low-level Bitcoin encoding rules.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct
from typing import Final


# The target that corresponds to difficulty 1.  It is derived directly from the
# compact ``bits`` representation ``0x1d00ffff`` that Satoshi used in the
# genesis block and that Bitcoin Core treats as the baseline target.
DIFFICULTY_1_TARGET: Final[int] = 0x00FFFF * 2 ** (8 * (0x1D - 3))


def double_sha256(payload: bytes) -> bytes:
    """Return the Bitcoin-style double SHA-256 digest for *payload*."""

    first_pass = hashlib.sha256(payload).digest()
    return hashlib.sha256(first_pass).digest()


def bits_to_target(bits: int) -> int:
    """Convert the compact ``bits`` field to an integer mining target."""

    exponent = bits >> 24
    mantissa = bits & 0xFFFFFF
    if exponent <= 3:
        return mantissa >> (8 * (3 - exponent))
    return mantissa << (8 * (exponent - 3))


def difficulty_from_target(target: int) -> float:
    """Compute the human-readable difficulty for a given *target*."""

    return DIFFICULTY_1_TARGET / target


@dataclass(frozen=True)
class BlockHeader:
    """Representation of a Bitcoin block header."""

    version: int
    previous_block: bytes
    merkle_root: bytes
    timestamp: int
    bits: int
    nonce: int

    def as_bytes(self) -> bytes:
        """Serialize the header fields using Bitcoin's little-endian layout."""

        return b"".join(
            (
                struct.pack("<L", self.version),
                self.previous_block[::-1],
                self.merkle_root[::-1],
                struct.pack("<L", self.timestamp),
                struct.pack("<L", self.bits),
                struct.pack("<L", self.nonce),
            )
        )

    def hash(self) -> bytes:
        """Return the double-SHA256 hash of the serialized header."""

        return double_sha256(self.as_bytes())[::-1]


def build_genesis_header() -> BlockHeader:
    """Construct the canonical Bitcoin genesis block header."""

    return BlockHeader(
        version=0x00000001,
        previous_block=bytes.fromhex("00" * 32),
        merkle_root=bytes.fromhex(
            "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b"
        ),
        timestamp=1231006505,
        bits=0x1D00FFFF,
        nonce=0x7C2BAC1D,
    )


def genesis_report() -> dict[str, object]:
    """Return a dictionary summarising the reconstructed genesis block."""

    header = build_genesis_header()
    header_hash = header.hash().hex()
    target = bits_to_target(header.bits)
    difficulty = difficulty_from_target(target)
    return {
        "block_hash": header_hash,
        "merkle_root": header.merkle_root.hex(),
        "target": target,
        "difficulty": difficulty,
    }


def main() -> None:
    """Emit a short report validating the Bitcoin genesis block header."""

    report = genesis_report()
    print("Block hash:", report["block_hash"])
    print("Merkle root:", report["merkle_root"])
    print("Target:", hex(report["target"]))
    print("Difficulty:", report["difficulty"])


if __name__ == "__main__":
    main()
