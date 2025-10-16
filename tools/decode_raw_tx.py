#!/usr/bin/env python3
"""Utility for decoding raw Bitcoin transactions.

This module implements a tiny parser for legacy and SegWit Bitcoin
transactions.  It accepts a hexadecimal transaction serialization and
returns a structured representation that is convenient for inspection or
programmatic use.

The implementation intentionally avoids external dependencies so the tool
can run in constrained environments.  Only the portions of the transaction
format that are required for inspection are implemented: version, inputs,
outputs, optional witness data, and locktime.  The parser also computes the
transaction identifier (txid) and the witness transaction identifier (wtxid)
when applicable.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
from typing import List, Sequence


def _read_varint(data: bytes, offset: int) -> tuple[int, int]:
    if offset >= len(data):
        raise ValueError("unexpected end of data while reading varint")

    prefix = data[offset]
    offset += 1

    if prefix < 0xFD:
        return prefix, offset

    size_map = {0xFD: 2, 0xFE: 4, 0xFF: 8}
    size = size_map.get(prefix)
    if size is None:
        raise ValueError(f"invalid varint prefix {prefix:#x}")

    if offset + size > len(data):
        raise ValueError("unexpected end of data while reading varint body")

    value = int.from_bytes(data[offset : offset + size], "little")
    offset += size
    return value, offset


def _encode_varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("varint value must be non-negative")
    if value < 0xFD:
        return bytes([value])
    if value <= 0xFFFF:
        return b"\xfd" + value.to_bytes(2, "little")
    if value <= 0xFFFFFFFF:
        return b"\xfe" + value.to_bytes(4, "little")
    return b"\xff" + value.to_bytes(8, "little")


@dataclasses.dataclass(slots=True)
class TxInput:
    prev_txid: str
    output_index: int
    script_sig: str
    sequence: int
    witness: List[str]


@dataclasses.dataclass(slots=True)
class TxOutput:
    value_satoshis: int
    script_pubkey: str


@dataclasses.dataclass(slots=True)
class DecodedTransaction:
    version: int
    inputs: List[TxInput]
    outputs: List[TxOutput]
    lock_time: int
    txid: str
    wtxid: str

    def to_json_dict(self) -> dict:
        return {
            "version": self.version,
            "lock_time": self.lock_time,
            "txid": self.txid,
            "wtxid": self.wtxid,
            "inputs": [
                {
                    "prev_txid": txin.prev_txid,
                    "output_index": txin.output_index,
                    "script_sig": txin.script_sig,
                    "sequence": txin.sequence,
                    "witness": txin.witness,
                }
                for txin in self.inputs
            ],
            "outputs": [
                {
                    "value_satoshis": txout.value_satoshis,
                    "script_pubkey": txout.script_pubkey,
                }
                for txout in self.outputs
            ],
        }


def _hash256(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def _serialise_without_witness(tx: DecodedTransaction) -> bytes:
    parts: List[bytes] = []
    parts.append(tx.version.to_bytes(4, "little", signed=True))
    parts.append(_encode_varint(len(tx.inputs)))
    for txin in tx.inputs:
        parts.append(bytes.fromhex(txin.prev_txid)[::-1])
        parts.append(txin.output_index.to_bytes(4, "little"))
        script_bytes = bytes.fromhex(txin.script_sig)
        parts.append(_encode_varint(len(script_bytes)))
        parts.append(script_bytes)
        parts.append(txin.sequence.to_bytes(4, "little"))
    parts.append(_encode_varint(len(tx.outputs)))
    for txout in tx.outputs:
        parts.append(txout.value_satoshis.to_bytes(8, "little"))
        script_bytes = bytes.fromhex(txout.script_pubkey)
        parts.append(_encode_varint(len(script_bytes)))
        parts.append(script_bytes)
    parts.append(tx.lock_time.to_bytes(4, "little"))
    return b"".join(parts)


def decode_raw_transaction(raw_hex: str) -> DecodedTransaction:
    raw_hex = raw_hex.strip()
    if len(raw_hex) % 2:
        raise ValueError("transaction hex length must be even")

    data = bytes.fromhex(raw_hex)
    cursor = 0

    if len(data) < 8:
        raise ValueError("transaction hex too short")

    version = int.from_bytes(data[cursor : cursor + 4], "little", signed=True)
    cursor += 4

    is_segwit = False
    if cursor + 2 <= len(data) and data[cursor] == 0 and data[cursor + 1] != 0:
        is_segwit = True
        cursor += 2  # marker and flag

    inputs: List[TxInput] = []
    input_count, cursor = _read_varint(data, cursor)
    for _ in range(input_count):
        if cursor + 36 > len(data):
            raise ValueError("unexpected end of data while reading input header")
        prev_txid = data[cursor : cursor + 32][::-1].hex()
        cursor += 32
        output_index = int.from_bytes(data[cursor : cursor + 4], "little")
        cursor += 4
        script_len, cursor = _read_varint(data, cursor)
        if cursor + script_len > len(data):
            raise ValueError("unexpected end of data while reading scriptSig")
        script_sig = data[cursor : cursor + script_len].hex()
        cursor += script_len
        if cursor + 4 > len(data):
            raise ValueError("unexpected end of data while reading sequence")
        sequence = int.from_bytes(data[cursor : cursor + 4], "little")
        cursor += 4
        inputs.append(TxInput(prev_txid, output_index, script_sig, sequence, []))

    outputs: List[TxOutput] = []
    output_count, cursor = _read_varint(data, cursor)
    for _ in range(output_count):
        if cursor + 8 > len(data):
            raise ValueError("unexpected end of data while reading output value")
        value = int.from_bytes(data[cursor : cursor + 8], "little")
        cursor += 8
        script_len, cursor = _read_varint(data, cursor)
        if cursor + script_len > len(data):
            raise ValueError("unexpected end of data while reading scriptPubKey")
        script_pubkey = data[cursor : cursor + script_len].hex()
        cursor += script_len
        outputs.append(TxOutput(value, script_pubkey))

    if is_segwit:
        for txin in inputs:
            item_count, cursor = _read_varint(data, cursor)
            witness_items: List[str] = []
            for _ in range(item_count):
                item_len, cursor = _read_varint(data, cursor)
                if cursor + item_len > len(data):
                    raise ValueError("unexpected end of data while reading witness")
                witness_items.append(data[cursor : cursor + item_len].hex())
                cursor += item_len
            txin.witness = witness_items

    if cursor + 4 > len(data):
        raise ValueError("unexpected end of data while reading lock_time")
    lock_time = int.from_bytes(data[cursor : cursor + 4], "little")
    cursor += 4

    if cursor != len(data):
        raise ValueError("extra data at end of transaction")

    decoded = DecodedTransaction(version, inputs, outputs, lock_time, "", "")

    serialised_no_witness = _serialise_without_witness(decoded)
    txid = _hash256(serialised_no_witness)[::-1].hex()
    wtxid = (
        _hash256(data)[::-1].hex() if is_segwit else txid
    )

    decoded.txid = txid
    decoded.wtxid = wtxid
    return decoded


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Decode a raw Bitcoin transaction")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--hex", help="Raw hexadecimal transaction string")
    source.add_argument("--file", help="Path to a file containing raw hex")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the decoded transaction as formatted JSON",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    if args.hex is not None:
        raw_hex = args.hex
    else:
        with open(args.file, "r", encoding="utf-8") as fh:
            raw_hex = fh.read()

    decoded = decode_raw_transaction(raw_hex)
    json_dict = decoded.to_json_dict()
    if args.pretty:
        print(json.dumps(json_dict, indent=2))
    else:
        print(json.dumps(json_dict))


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
