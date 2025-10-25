"""Deterministic reconstruction of the Bitcoin genesis block header.

This helper recomputes the merkle root from the canonical coinbase
transaction published on 3 January 2009 and then rebuilds the full block
header. The resulting hash is compared to the historical value
`000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f`.

Running the script should always emit identical digests. Any deviation
implies that either the embedded transaction payload has been tampered
with or your Python interpreter is malfunctioning.
"""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass

GENESIS_COINBASE_HEX = (
    "01000000010000000000000000000000000000000000000000000000000000000000000000"
    "ffffffff4d04ffff001d0104455468652054696d65732030332f4a616e2f32303039204368"
    "616e63656c6c6f72206f6e206272696e6b206f66207365636f6e64206261696c6f75742066"
    "6f722062616e6b73ffffffff0100f2052a01000000434104678afdb0fe5548271967f1a671"
    "30b7105cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef38c4f35504e51ec112de5c38"
    "4df7ba0b8d578a4c702b6bf11d5fac00000000"
)

GENESIS_PREVIOUS_BLOCK = "00" * 32
GENESIS_TIMESTAMP = 1231006505
GENESIS_BITS = 0x1D00FFFF
GENESIS_NONCE = 2083236893


@dataclass(frozen=True)
class GenesisProof:
    coinbase_hex: str
    tx_hash: str
    merkle_root: str
    block_hash: str

    def as_dict(self) -> dict[str, str]:
        return {
            "coinbase_hex": self.coinbase_hex,
            "tx_hash": self.tx_hash,
            "merkle_root": self.merkle_root,
            "block_hash": self.block_hash,
        }


def double_sha256(payload: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(payload).digest()).digest()


def little_endian_hex(raw: bytes) -> str:
    return raw[::-1].hex()


def recompute_genesis() -> GenesisProof:
    coinbase_bytes = bytes.fromhex(GENESIS_COINBASE_HEX)
    tx_hash_le = double_sha256(coinbase_bytes)

    header = b"".join(
        (
            (1).to_bytes(4, "little"),
            bytes.fromhex(GENESIS_PREVIOUS_BLOCK)[::-1],
            tx_hash_le,
            GENESIS_TIMESTAMP.to_bytes(4, "little"),
            GENESIS_BITS.to_bytes(4, "little"),
            GENESIS_NONCE.to_bytes(4, "little"),
        )
    )

    block_hash_le = double_sha256(header)

    return GenesisProof(
        coinbase_hex=GENESIS_COINBASE_HEX,
        tx_hash=little_endian_hex(tx_hash_le),
        merkle_root=little_endian_hex(tx_hash_le),
        block_hash=little_endian_hex(block_hash_le),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the reconstructed proof as JSON",
    )
    args = parser.parse_args()

    proof = recompute_genesis()

    if args.json:
        import json

        print(json.dumps(proof.as_dict(), indent=2))
        return

    print("Genesis coinbase (hex):")
    print(proof.coinbase_hex)
    print()
    print("Transaction hash (big-endian):", proof.tx_hash)
    print("Merkle root (big-endian):    ", proof.merkle_root)
    print("Block hash (big-endian):     ", proof.block_hash)

    reference_hash = (
        "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"
    )
    if proof.block_hash != reference_hash:
        raise SystemExit(
            "Block hash mismatch — the embedded data no longer matches "
            "the historical genesis block"
        )


if __name__ == "__main__":
    main()
