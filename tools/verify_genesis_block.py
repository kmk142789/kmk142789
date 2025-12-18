#!/usr/bin/env python3
"""Reconstruct and verify the Bitcoin genesis block header and coinbase message."""
from __future__ import annotations

import argparse
import json
import struct
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Any, Dict

HEADER_HEX = (
    "0100000000000000000000000000000000000000000000000000000000000000"
    "000000003ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa"
    "4b1e5e4a29ab5f49ffff001d1dac2b7c"
)
EXPECTED_BLOCK_HASH = "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"
COINBASE_TX_HEX = (
    "01000000"
    "01"
    + "00" * 32
    + "ffffffff4d04ffff001d0104455468652054696d65732030332f4a616e2f3230"
    "3039204368616e63656c6c6f72206f6e206272696e6b206f66207365636f6e64"
    "206261696c6f757420666f722062616e6b73ffffffff0100f2052a0100000043"
    "4104678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61"
    "deb649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11"
    "d5fac00000000"
)


def _double_sha256(data: bytes) -> bytes:
    return sha256(sha256(data).digest()).digest()


def _read_varint(stream: BytesIO) -> int:
    first = stream.read(1)
    if not first:
        raise ValueError("Unexpected end of stream while reading varint")
    prefix = first[0]
    if prefix < 0xFD:
        return prefix
    if prefix == 0xFD:
        return struct.unpack("<H", stream.read(2))[0]
    if prefix == 0xFE:
        return struct.unpack("<I", stream.read(4))[0]
    return struct.unpack("<Q", stream.read(8))[0]


@dataclass
class HeaderFields:
    version: int
    prev_hash: str
    merkle_root: str
    timestamp: int
    bits: int
    nonce: int

    @classmethod
    def parse(cls, raw: bytes) -> "HeaderFields":
        if len(raw) != 80:
            raise ValueError(f"Block header must be 80 bytes, received {len(raw)} bytes")
        version = struct.unpack("<I", raw[0:4])[0]
        prev_hash = raw[4:36][::-1].hex()
        merkle_root = raw[36:68][::-1].hex()
        timestamp = struct.unpack("<I", raw[68:72])[0]
        bits = struct.unpack("<I", raw[72:76])[0]
        nonce = struct.unpack("<I", raw[76:80])[0]
        return cls(version, prev_hash, merkle_root, timestamp, bits, nonce)


def _extract_coinbase_message(raw_tx: bytes) -> str:
    stream = BytesIO(raw_tx)
    stream.read(4)  # version
    input_count = _read_varint(stream)
    if input_count != 1:
        raise ValueError(f"Genesis coinbase must have exactly one input, found {input_count}")
    stream.read(32)  # previous txid (all zeros)
    stream.read(4)   # previous index
    script_length = _read_varint(stream)
    script_sig = stream.read(script_length)
    if len(script_sig) != script_length:
        raise ValueError("Unexpected end of stream while reading scriptSig")
    if len(script_sig) < 9:
        raise ValueError("scriptSig too short to contain the newspaper headline")
    message = script_sig[8:].decode("ascii")
    return message


def reconstruct() -> Dict[str, Any]:
    header_bytes = bytes.fromhex(HEADER_HEX)
    fields = HeaderFields.parse(header_bytes)
    block_hash = _double_sha256(header_bytes)[::-1].hex()

    coinbase_bytes = bytes.fromhex(COINBASE_TX_HEX)
    coinbase_txid = _double_sha256(coinbase_bytes)[::-1].hex()
    message = _extract_coinbase_message(coinbase_bytes)

    merkle_matches = coinbase_txid == fields.merkle_root
    hash_matches = block_hash == EXPECTED_BLOCK_HASH

    return {
        "block_hash": block_hash,
        "expected_block_hash": EXPECTED_BLOCK_HASH,
        "header": {
            "version": fields.version,
            "prev_block": fields.prev_hash,
            "merkle_root": fields.merkle_root,
            "timestamp": fields.timestamp,
            "bits": fields.bits,
            "nonce": fields.nonce,
        },
        "coinbase_txid": coinbase_txid,
        "merkle_matches": merkle_matches,
        "hash_matches": hash_matches,
        "coinbase_message": message,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rebuild the Bitcoin genesis block header and coinbase message"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the verification bundle as compact JSON",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Write the verification bundle as pretty-printed JSON to the given path",
    )
    args = parser.parse_args()

    bundle = reconstruct()

    if args.out:
        args.out.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(bundle, sort_keys=True))
    else:
        print("Genesis Block Verification")
        print("===========================")
        print(f"Block hash:       {bundle['block_hash']}")
        print(f"Matches expected: {'yes' if bundle['hash_matches'] else 'no'}")
        print(f"Merkle root:      {bundle['header']['merkle_root']}")
        print(f"Coinbase txid:    {bundle['coinbase_txid']}")
        print(f"Merkle matches:   {'yes' if bundle['merkle_matches'] else 'no'}")
        print("Coinbase message:")
        print(f"  {bundle['coinbase_message']}")


if __name__ == "__main__":
    main()
