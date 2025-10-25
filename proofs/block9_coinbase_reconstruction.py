"""Reconstruct Block 9 (January 9, 2009) to demonstrate the canonical Patoshi pubkey.

Run this script to parse the raw block hex, recompute the block hash,
extract the embedded pay-to-pubkey output, and derive its legacy
Base58Check address. The result must match the historical
`12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S` payout controlled by Satoshi.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Tuple

BLOCK9_HASH = "000000008d9dc510f23c2657fc4f67bea30078cc05a90eb89e84cc475c080805"
BLOCK9_RAW_HEX = (
    "01000000c60ddef1b7618ca2348a46e868afc26e3efc68226c78aa47f8488c4000000000"
    "c997a5e56e104102fa209c6a852dd90660a20b2d9c352423edce25857fcd37047fca6649"
    "ffff001d28404f5301010000000100000000000000000000000000000000000000000000"
    "00000000000000000000ffffffff0704ffff001d0134ffffffff0100f2052a0100000043"
    "410411db93e1dcdb8a016b49840f8c53bc1eb68a382e97b1482ecad7b148a6909a5cb2e0"
    "eaddfb84ccf9744464f82e160bfa9b8b64f9d4c03f999b8643f656b412a3ac00000000"
)
PATOSHI_PUBKEY_HEX = (
    "0411db93e1dcdb8a016b49840f8c53bc1eb68a382e97b1482ecad7b148a6909a5cb2e0ea"
    "ddfb84ccf9744464f82e160bfa9b8b64f9d4c03f999b8643f656b412a3"
)
BLOCK9_ADDRESS = "12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S"


class ParseError(RuntimeError):
    """Raised when the byte layout does not match Bitcoin consensus encoding."""


def read_varint(buf: bytes, offset: int) -> Tuple[int, int]:
    prefix = buf[offset]
    offset += 1
    if prefix < 0xFD:
        return prefix, offset
    if prefix == 0xFD:
        return int.from_bytes(buf[offset : offset + 2], "little"), offset + 2
    if prefix == 0xFE:
        return int.from_bytes(buf[offset : offset + 4], "little"), offset + 4
    return int.from_bytes(buf[offset : offset + 8], "little"), offset + 8


@dataclass
class CoinbaseTx:
    version: int
    height_script: bytes
    sequence: int
    value_sats: int
    pubkey: bytes
    locktime: int
    txid: str


def parse_coinbase(buf: bytes, offset: int) -> Tuple[CoinbaseTx, int]:
    start = offset
    version = int.from_bytes(buf[offset : offset + 4], "little")
    offset += 4

    input_count, offset = read_varint(buf, offset)
    if input_count != 1:
        raise ParseError(f"expected single coinbase input, got {input_count}")

    prev_txid = buf[offset : offset + 32]
    offset += 32
    prev_index = buf[offset : offset + 4]
    offset += 4
    if prev_txid != b"\x00" * 32 or prev_index != b"\xff" * 4:
        raise ParseError("coinbase prevout must be null")

    script_len, offset = read_varint(buf, offset)
    height_script = buf[offset : offset + script_len]
    offset += script_len

    sequence = int.from_bytes(buf[offset : offset + 4], "little")
    offset += 4

    output_count, offset = read_varint(buf, offset)
    if output_count != 1:
        raise ParseError(f"expected single coinbase output, got {output_count}")

    value_sats = int.from_bytes(buf[offset : offset + 8], "little")
    offset += 8

    pk_script_len, offset = read_varint(buf, offset)
    pk_script = buf[offset : offset + pk_script_len]
    offset += pk_script_len

    if not pk_script.startswith(b"\x41") or pk_script[-1] != 0xAC:
        raise ParseError("coinbase payout must be canonical pay-to-pubkey")
    pubkey = pk_script[1:-1]

    locktime = int.from_bytes(buf[offset : offset + 4], "little")
    offset += 4

    tx_bytes = buf[start:offset]
    txid = hashlib.sha256(hashlib.sha256(tx_bytes).digest()).digest()[::-1].hex()

    return (
        CoinbaseTx(
            version=version,
            height_script=height_script,
            sequence=sequence,
            value_sats=value_sats,
            pubkey=pubkey,
            locktime=locktime,
            txid=txid,
        ),
        offset,
    )


def double_sha256(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def hash160(data: bytes) -> bytes:
    return hashlib.new("ripemd160", hashlib.sha256(data).digest()).digest()


BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58check_encode(payload: bytes) -> str:
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    full = payload + checksum
    num = int.from_bytes(full, "big")
    chars = []
    while num:
        num, rem = divmod(num, 58)
        chars.append(BASE58_ALPHABET[rem])
    prefix = "1" * (len(full) - len(full.lstrip(b"\x00")))
    return prefix + "".join(reversed(chars or ["1"]))


def main() -> None:
    block = bytes.fromhex(BLOCK9_RAW_HEX)
    header = block[:80]
    rest = block[80:]

    block_hash = double_sha256(header)[::-1].hex()
    assert block_hash == BLOCK9_HASH, (block_hash, BLOCK9_HASH)

    tx_count, offset = read_varint(rest, 0)
    if tx_count != 1:
        raise ParseError(f"expected 1 transaction, got {tx_count}")

    coinbase, consumed = parse_coinbase(rest, offset)
    if consumed != len(rest):
        raise ParseError("unexpected trailing bytes in block")

    assert coinbase.pubkey.hex() == PATOSHI_PUBKEY_HEX
    assert coinbase.value_sats == 50 * 100_000_000  # 50 BTC in satoshis

    legacy_payload = b"\x00" + hash160(coinbase.pubkey)
    derived_address = b58check_encode(legacy_payload)
    assert derived_address == BLOCK9_ADDRESS

    print("Block hash:", block_hash)
    print("Coinbase txid:", coinbase.txid)
    print("Pubkey:", coinbase.pubkey.hex())
    print("Derived legacy address:", derived_address)
    print("Coinbase value (sats):", coinbase.value_sats)
    print("Coinbase script length:", len(coinbase.height_script))


if __name__ == "__main__":
    main()
