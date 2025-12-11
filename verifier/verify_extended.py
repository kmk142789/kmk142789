#!/usr/bin/env python3
"""Validate address/pubkey pairs from a CSV dataset.

The script checks that each address corresponds to the provided
compressed or uncompressed public key. Supported formats:

* Bitcoin mainnet/testnet P2PKH (base58check, leading ``1`` or ``m/n``)
* Bech32 P2WPKH (``bc1``/``tb1`` witness version 0, 20-byte program)

Each CSV row must contain ``address,pubkey_hex``. Blank lines and lines
starting with ``#`` are ignored.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from dataclasses import dataclass
from typing import Iterable, List, Tuple

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


@dataclass
class VerificationResult:
    line_no: int
    address: str
    pubkey: str
    valid: bool
    reason: str | None = None


def hash160(data: bytes) -> bytes:
    sha = hashlib.sha256(data).digest()
    ripe = hashlib.new("ripemd160", sha).digest()
    return ripe


def _b58decode_check(addr: str) -> bytes:
    num = 0
    for char in addr:
        try:
            num = num * 58 + BASE58_ALPHABET.index(char)
        except ValueError as exc:
            raise ValueError(f"invalid base58 character: {char!r}") from exc

    combined = num.to_bytes((num.bit_length() + 7) // 8, "big")
    leading = 0
    for char in addr:
        if char == "1":
            leading += 1
        else:
            break
    combined = b"\x00" * leading + combined

    if len(combined) < 4:
        raise ValueError("address too short")

    payload, checksum = combined[:-4], combined[-4:]
    expected = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    if checksum != expected:
        raise ValueError("checksum mismatch")
    return payload


# ---- bech32 decoding (adapted from BIP-0173 reference implementation) ----
_BECH32_ALPHABET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_BECH32_ALPHABET_MAP = {c: i for i, c in enumerate(_BECH32_ALPHABET)}
_BECH32_CONST = 1
_BECH32M_CONST = 0x2BC830A3


def _bech32_polymod(values: Iterable[int]) -> int:
    generator = (0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3)
    chk = 1
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1FFFFFF) << 5 ^ value
        for i in range(5):
            if (top >> i) & 1:
                chk ^= generator[i]
    return chk


def _bech32_hrp_expand(hrp: str) -> List[int]:
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def _bech32_verify_checksum(hrp: str, data: List[int]) -> tuple[str, int]:
    """Return checksum encoding and polymod result.

    The checksum constant distinguishes bech32 (1) from bech32m
    (0x2BC830A3).  Returning the encoding string lets callers enforce
    the witness version rules from BIP-0173/350.
    """

    polymod = _bech32_polymod(_bech32_hrp_expand(hrp) + data)
    if polymod == _BECH32_CONST:
        return "bech32", polymod
    if polymod == _BECH32M_CONST:
        return "bech32m", polymod
    raise ValueError("invalid checksum")


def _bech32_create_checksum(hrp: str, data: List[int], *, encoding: str) -> List[int]:
    const = _BECH32M_CONST if encoding == "bech32m" else _BECH32_CONST
    values = _bech32_hrp_expand(hrp) + data
    polymod = _bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ const
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]


def _convertbits(data: Iterable[int], from_bits: int, to_bits: int, *, pad: bool = True) -> List[int]:
    acc = 0
    bits = 0
    result: List[int] = []
    maxv = (1 << to_bits) - 1
    max_acc = (1 << (from_bits + to_bits - 1)) - 1
    for value in data:
        if value < 0 or value >> from_bits:
            raise ValueError("invalid data range")
        acc = (acc << from_bits) | value
        bits += from_bits
        while bits >= to_bits:
            bits -= to_bits
            result.append((acc >> bits) & maxv)
    if pad:
        if bits:
            result.append((acc << (to_bits - bits)) & maxv)
    elif bits >= from_bits or (acc << (to_bits - bits)) & maxv:
        raise ValueError("invalid padding")
    return result


def _bech32_decode(addr: str) -> Tuple[str, int, bytes, str]:
    if not addr.lower().startswith(("bc1", "tb1", "bcrt1")):
        raise ValueError("unsupported HRP")

    if any(ord(char) < 33 or ord(char) > 126 for char in addr):
        raise ValueError("invalid characters")

    addr = addr.lower()
    if addr.rfind("1") == -1:
        raise ValueError("missing separator")

    hrp, data_part = addr.split("1", 1)
    if not hrp or not data_part:
        raise ValueError("invalid format")

    try:
        data = [_BECH32_ALPHABET_MAP[c] for c in data_part]
    except KeyError as exc:
        raise ValueError(f"invalid Bech32 character: {exc.args[0]}") from exc

    encoding, _ = _bech32_verify_checksum(hrp, data)

    values = data[:-6]
    if not values:
        raise ValueError("empty data section")

    witness_version = values[0]
    if witness_version > 16:
        raise ValueError("invalid witness version")
    program = bytes(_convertbits(values[1:], 5, 8, pad=False))
    return hrp, witness_version, program, encoding


# ---------------------------------------------------------------------------

def _validate_pair(address: str, pubkey_hex: str) -> Tuple[bool, str | None]:
    try:
        pubkey = bytes.fromhex(pubkey_hex)
    except ValueError:
        return False, "pubkey is not valid hex"

    if len(pubkey) not in (32, 33, 65):
        return False, "unexpected pubkey length"

    pkh = hash160(pubkey)

    if address.startswith("1") or address.startswith("m") or address.startswith("n"):
        try:
            payload = _b58decode_check(address)
        except ValueError as exc:
            return False, str(exc)
        if len(payload) != 21:
            return False, "unexpected base58 payload length"
        version, h160 = payload[0], payload[1:]
        if version not in (0x00, 0x6F):
            return False, f"unsupported version {version}"
        return (h160 == pkh, None if h160 == pkh else "hash160 mismatch")

    if address.lower().startswith(("bc1", "tb1")):
        try:
            _, version, program, encoding = _bech32_decode(address)
        except ValueError as exc:
            return False, str(exc)
        if version == 0:
            if encoding != "bech32":
                return False, "version 0 witness addresses require bech32"
            if len(program) != 20:
                return False, f"unexpected witness length {len(program)}"
            return (program == pkh, None if program == pkh else "witness mismatch")

        if version == 1:
            if encoding != "bech32m":
                return False, "version 1 witness addresses require bech32m"
            if len(program) != 32:
                return False, f"unexpected witness length {len(program)}"
            xonly = pubkey if len(pubkey) == 32 else pubkey[1:33]
            return (program == xonly, None if program == xonly else "taproot mismatch")

        return False, f"unsupported witness version {version}"

    return False, "unsupported address format"


def iter_rows(path: str) -> Iterable[Tuple[int, str, str]]:
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for idx, row in enumerate(reader, start=1):
            if not row:
                continue
            if row[0].startswith("#"):
                continue
            if len(row) < 2:
                raise ValueError(f"line {idx}: expected address,pubkey")
            yield idx, row[0].strip(), row[1].strip()


def verify_dataset(path: str, *, max_errors: int | None = None) -> List[VerificationResult]:
    results: List[VerificationResult] = []
    errors = 0
    for line_no, address, pubkey in iter_rows(path):
        valid, reason = _validate_pair(address, pubkey)
        if not valid:
            errors += 1
        results.append(VerificationResult(line_no, address, pubkey, valid, reason))
        if max_errors is not None and errors >= max_errors:
            break
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify address/pubkey mappings")
    parser.add_argument("dataset", help="CSV file with address,pubkey")
    parser.add_argument("--max-errors", type=int, default=None, help="stop after this many failures")
    args = parser.parse_args(argv)

    try:
        results = verify_dataset(args.dataset, max_errors=args.max_errors)
    except Exception as exc:  # pragma: no cover - CLI convenience
        print(f"error: {exc}", file=sys.stderr)
        return 2

    total = len(results)
    valid = sum(1 for item in results if item.valid)
    invalid = total - valid

    print(f"Checked {total} rows → {valid} valid, {invalid} invalid")
    for item in results:
        if not item.valid:
            reason = f" ({item.reason})" if item.reason else ""
            print(f"  line {item.line_no}: {item.address} ✕{reason}")

    return 0 if invalid == 0 else 1


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
