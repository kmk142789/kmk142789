#!/usr/bin/env python3
"""Verify the genesis block coinbase message embedded by Satoshi Nakamoto.

This script validates a JSON proof file that contains the raw transaction,
block header, and decoded newspaper headline from the Bitcoin genesis block.
It performs three independent checks:

1. Recomputes the transaction ID from the raw coinbase transaction bytes.
2. Confirms the block header double-SHA256 hash equals the published block hash
   and that the merkle root matches the coinbase txid.
3. Parses the coinbase scriptSig to extract the embedded newspaper headline and
   verifies that it matches the canonical text:
   "The Times 03/Jan/2009 Chancellor on brink of second bailout for banks".

Usage:
    python tools/verify_genesis_coinbase.py [path/to/proof.json]

The proof file defaults to ``proofs/genesis_coinbase_message.json``.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import io
import json
from typing import List


GENESIS_HEADLINE = (
    "The Times 03/Jan/2009 Chancellor on brink of second bailout for banks"
)


@dataclasses.dataclass
class GenesisProof:
    block_height: int
    block_hash: str
    block_header_hex: str
    merkle_root: str
    coinbase_txid: str
    coinbase_raw_hex: str
    coinbase_scriptsig_hex: str
    headline: str

    @classmethod
    def from_json(cls, path: str) -> "GenesisProof":
        with open(path, "r", encoding="utf-8") as infile:
            payload = json.load(infile)
        return cls(**payload)


def double_sha256(data: bytes) -> bytes:
    """Return the double-SHA256 digest of ``data``."""

    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def read_varint(stream: io.BytesIO) -> int:
    """Decode a Bitcoin-style variable length integer."""

    raw = stream.read(1)
    if not raw:
        raise ValueError("Unexpected EOF while reading varint")
    prefix = raw[0]
    if prefix < 0xFD:
        return prefix
    if prefix == 0xFD:
        return int.from_bytes(stream.read(2), "little")
    if prefix == 0xFE:
        return int.from_bytes(stream.read(4), "little")
    return int.from_bytes(stream.read(8), "little")


def parse_pushdata(script: bytes) -> List[bytes]:
    """Extract pushdata fields from a Bitcoin script."""

    pushes: List[bytes] = []
    index = 0
    length = len(script)
    while index < length:
        opcode = script[index]
        index += 1
        if opcode <= 75:
            pushes.append(script[index : index + opcode])
            index += opcode
        elif opcode == 76:  # OP_PUSHDATA1
            size = script[index]
            index += 1
            pushes.append(script[index : index + size])
            index += size
        elif opcode == 77:  # OP_PUSHDATA2
            size = int.from_bytes(script[index : index + 2], "little")
            index += 2
            pushes.append(script[index : index + size])
            index += size
        elif opcode == 78:  # OP_PUSHDATA4
            size = int.from_bytes(script[index : index + 4], "little")
            index += 4
            pushes.append(script[index : index + size])
            index += size
        else:
            raise ValueError(f"Unsupported opcode 0x{opcode:02x} in script")
    return pushes


def extract_coinbase_message(raw_tx: bytes) -> str:
    """Parse the genesis coinbase transaction and return the embedded headline."""

    stream = io.BytesIO(raw_tx)

    # Transaction version (4 bytes)
    _ = stream.read(4)

    # Inputs
    input_count = read_varint(stream)
    if input_count != 1:
        raise ValueError(f"Unexpected coinbase input count: {input_count}")

    # Coinbase input
    _ = stream.read(32)  # previous tx hash
    _ = stream.read(4)  # previous output index
    script_length = read_varint(stream)
    script_sig = stream.read(script_length)
    _ = stream.read(4)  # sequence

    pushes = parse_pushdata(script_sig)
    if not pushes:
        raise ValueError("Coinbase scriptSig missing pushdata fields")

    message_bytes = pushes[-1]
    try:
        message = message_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:  # pragma: no cover - should not happen
        raise ValueError("Coinbase message is not valid UTF-8") from exc
    return message


def verify_genesis_proof(proof: GenesisProof) -> None:
    raw_tx = bytes.fromhex(proof.coinbase_raw_hex)
    calculated_txid = double_sha256(raw_tx)[::-1].hex()
    if calculated_txid != proof.coinbase_txid:
        raise SystemExit(
            f"Coinbase txid mismatch: expected {proof.coinbase_txid}, got {calculated_txid}"
        )

    header_bytes = bytes.fromhex(proof.block_header_hex)
    calculated_block_hash = double_sha256(header_bytes)[::-1].hex()
    if calculated_block_hash != proof.block_hash:
        raise SystemExit(
            f"Block hash mismatch: expected {proof.block_hash}, got {calculated_block_hash}"
        )

    # The merkle root in the header is stored little-endian.
    merkle_from_header = header_bytes[36:68][::-1].hex()
    if merkle_from_header != proof.merkle_root:
        raise SystemExit(
            "Merkle root mismatch between header and proof file"
        )

    if proof.merkle_root != proof.coinbase_txid:
        raise SystemExit(
            "Merkle root does not match the single coinbase transaction id"
        )

    extracted_message = extract_coinbase_message(raw_tx)
    if extracted_message != GENESIS_HEADLINE:
        raise SystemExit(
            "Extracted coinbase headline does not match the canonical Genesis message"
        )

    if proof.headline != GENESIS_HEADLINE:
        raise SystemExit(
            "Headline in proof file differs from canonical Genesis message"
        )

    print("✔ Genesis block coinbase headline verified.")
    print(f"  Block hash: {proof.block_hash}")
    print(f"  Coinbase txid: {proof.coinbase_txid}")
    print(f"  Headline: {GENESIS_HEADLINE}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "proof_path",
        nargs="?",
        default="proofs/genesis_coinbase_message.json",
        help="Path to the JSON proof payload",
    )
    args = parser.parse_args()

    proof = GenesisProof.from_json(args.proof_path)
    verify_genesis_proof(proof)


if __name__ == "__main__":
    main()
