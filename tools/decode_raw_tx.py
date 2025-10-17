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
from typing import Iterable, List, Mapping, Sequence


_NETWORKS: Mapping[str, Mapping[str, object]] = {
    "mainnet": {"p2pkh": 0x00, "p2sh": 0x05, "bech32_hrp": "bc"},
    "testnet": {"p2pkh": 0x6F, "p2sh": 0xC4, "bech32_hrp": "tb"},
    "regtest": {"p2pkh": 0x6F, "p2sh": 0xC4, "bech32_hrp": "bcrt"},
}

_BASE58_ALPHABET = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BECH32_ALPHABET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_BECH32_GENERATORS = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]


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
    address: str | None = None


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
                    "address": txout.address,
                }
                for txout in self.outputs
            ],
        }


def _hash256(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def _base58check_encode(version: int, payload: bytes) -> str:
    data = bytes([version]) + payload
    checksum = _hash256(data)[:4]
    encoded_int = int.from_bytes(data + checksum, "big")
    chars = bytearray()
    while encoded_int:
        encoded_int, remainder = divmod(encoded_int, 58)
        chars.append(_BASE58_ALPHABET[remainder])
    if not chars:
        chars.append(_BASE58_ALPHABET[0])
    chars.reverse()
    pad = 0
    for byte in data + checksum:
        if byte == 0:
            pad += 1
        else:
            break
    return (b"1" * pad + bytes(chars)).decode("ascii")


def _bech32_polymod(values: Iterable[int]) -> int:
    chk = 1
    for value in values:
        top = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ value
        for i, generator in enumerate(_BECH32_GENERATORS):
            if (top >> i) & 1:
                chk ^= generator
    return chk


def _bech32_hrp_expand(hrp: str) -> List[int]:
    return [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]


def _convertbits(data: bytes, from_bits: int, to_bits: int, pad: bool = True) -> List[int]:
    acc = 0
    bits = 0
    result: List[int] = []
    max_value = (1 << to_bits) - 1
    max_acc = (1 << (from_bits + to_bits - 1)) - 1
    for value in data:
        if value < 0 or value >> from_bits:
            raise ValueError("invalid value for convertbits")
        acc = ((acc << from_bits) | value) & max_acc
        bits += from_bits
        while bits >= to_bits:
            bits -= to_bits
            result.append((acc >> bits) & max_value)
    if pad:
        if bits:
            result.append((acc << (to_bits - bits)) & max_value)
    elif bits >= from_bits or ((acc << (to_bits - bits)) & max_value):
        raise ValueError("invalid padding in convertbits")
    return result


def _create_bech32_checksum(hrp: str, data: Sequence[int], const: int) -> List[int]:
    values = _bech32_hrp_expand(hrp) + list(data)
    polymod = _bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ const
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]


def _encode_segwit_address(hrp: str, witness_version: int, program: bytes) -> str | None:
    if not (0 <= witness_version <= 16):
        return None
    if not (2 <= len(program) <= 40):
        return None
    try:
        data = [witness_version] + _convertbits(program, 8, 5, pad=True)
    except ValueError:
        return None
    const = 1 if witness_version == 0 else 0x2BC830A3
    checksum = _create_bech32_checksum(hrp, data, const)
    combined = data + checksum
    return hrp + "1" + "".join(_BECH32_ALPHABET[d] for d in combined)


def _decode_script_pubkey(script: bytes, network: Mapping[str, object]) -> str | None:
    if len(script) == 25 and script.startswith(b"\x76\xA9\x14") and script.endswith(b"\x88\xAC"):
        return _base58check_encode(int(network["p2pkh"]), script[3:-2])
    if len(script) == 23 and script.startswith(b"\xA9\x14") and script.endswith(b"\x87"):
        return _base58check_encode(int(network["p2sh"]), script[2:-1])
    if len(script) >= 4 and script[1] == len(script) - 2:
        opcode = script[0]
        if opcode == 0x00:
            witness_version = 0
        elif 0x51 <= opcode <= 0x60:
            witness_version = opcode - 0x50
        else:
            witness_version = None
        if witness_version is not None:
            program = script[2:]
            hrp = str(network["bech32_hrp"])
            return _encode_segwit_address(hrp, witness_version, program)
    return None


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


def decode_raw_transaction(raw_hex: str, network: str = "mainnet") -> DecodedTransaction:
    raw_hex = raw_hex.strip()
    if len(raw_hex) % 2:
        raise ValueError("transaction hex length must be even")

    data = bytes.fromhex(raw_hex)
    cursor = 0

    if len(data) < 8:
        raise ValueError("transaction hex too short")

    network_info = _NETWORKS.get(network)
    if network_info is None:
        raise ValueError(f"unknown network '{network}'")

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
        script_bytes = data[cursor : cursor + script_len]
        script_pubkey = script_bytes.hex()
        cursor += script_len
        address = _decode_script_pubkey(script_bytes, network_info)
        outputs.append(TxOutput(value, script_pubkey, address))

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
        "--network",
        choices=tuple(_NETWORKS.keys()),
        default="mainnet",
        help="Bitcoin network used for address decoding (default: mainnet)",
    )
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

    decoded = decode_raw_transaction(raw_hex, network=args.network)
    json_dict = decoded.to_json_dict()
    if args.pretty:
        print(json.dumps(json_dict, indent=2))
    else:
        print(json.dumps(json_dict))


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
