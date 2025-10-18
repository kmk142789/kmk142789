#!/usr/bin/env python3
"""Verify Bitcoin puzzle message signatures.

This utility accepts an address, message, and a signature string.
The signature string may contain multiple base64-encoded segments
concatenated together (e.g. separated by '=' characters). Each
segment is treated as a candidate signature and verified using the
standard Bitcoin message verification routine.

Outputs a JSON object summarizing which segments validate.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional

_SECP256K1_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_SECP256K1_GX = 55066263022277343669578718895168534326250603453777594175500187360389116729240
_SECP256K1_GY = 32670510020758816978083085130507043184471273380659243275938904335757337482424
_SECP256K1_G = (_SECP256K1_GX, _SECP256K1_GY)


@dataclass
class SignatureCheckResult:
    """Result for a single signature segment."""

    index: int
    signature: str
    valid: bool
    derived_address: Optional[str] = None

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "signature": self.signature,
            "valid": self.valid,
            "derived_address": self.derived_address,
        }


BASE64_SEGMENT_PATTERN = re.compile(r"[A-Za-z0-9+/]+={0,2}")

BASE58_ALPHABET = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def encode_varint(n: int) -> bytes:
    if n < 0xFD:
        return bytes([n])
    if n <= 0xFFFF:
        return b"\xfd" + n.to_bytes(2, "little")
    if n <= 0xFFFFFFFF:
        return b"\xfe" + n.to_bytes(4, "little")
    return b"\xff" + n.to_bytes(8, "little")


def bitcoin_message_hash(message: str) -> bytes:
    payload = (
        b"\x18Bitcoin Signed Message:\n"
        + encode_varint(len(message.encode("utf-8")))
        + message.encode("utf-8")
    )
    return hashlib.sha256(hashlib.sha256(payload).digest()).digest()


def b58encode(data: bytes) -> bytes:
    # Strip leading zeros for encoding but preserve count for prefixing
    zeros = len(data) - len(data.lstrip(b"\x00"))
    num = int.from_bytes(data, "big")
    encoded = bytearray()
    while num > 0:
        num, rem = divmod(num, 58)
        encoded.append(BASE58_ALPHABET[rem])
    encoded.extend(b"1" * zeros)
    return bytes(reversed(encoded))


def _inverse_mod(value: int, modulus: int) -> int:
    return pow(value, -1, modulus)


def _point_add(
    point_a: Optional[tuple[int, int]], point_b: Optional[tuple[int, int]]
) -> Optional[tuple[int, int]]:
    if point_a is None:
        return point_b
    if point_b is None:
        return point_a
    if point_a[0] == point_b[0] and (point_a[1] + point_b[1]) % _SECP256K1_P == 0:
        return None
    if point_a == point_b:
        slope = (3 * point_a[0] * point_a[0]) * _inverse_mod(2 * point_a[1], _SECP256K1_P)
    else:
        slope = (point_b[1] - point_a[1]) * _inverse_mod(point_b[0] - point_a[0], _SECP256K1_P)
    slope %= _SECP256K1_P
    x_r = (slope * slope - point_a[0] - point_b[0]) % _SECP256K1_P
    y_r = (slope * (point_a[0] - x_r) - point_a[1]) % _SECP256K1_P
    return x_r, y_r


def _point_neg(point: Optional[tuple[int, int]]) -> Optional[tuple[int, int]]:
    if point is None:
        return None
    return point[0], (-point[1]) % _SECP256K1_P


def _point_sub(
    point_a: Optional[tuple[int, int]], point_b: Optional[tuple[int, int]]
) -> Optional[tuple[int, int]]:
    return _point_add(point_a, _point_neg(point_b))


def _scalar_multiply(k: int, point: tuple[int, int]) -> Optional[tuple[int, int]]:
    result: Optional[tuple[int, int]] = None
    addend: Optional[tuple[int, int]] = point
    while k:
        if k & 1:
            result = _point_add(result, addend)
        addend = _point_add(addend, addend)
        k >>= 1
    return result


def _lift_x(x: int, odd: int) -> Optional[tuple[int, int]]:
    if x >= _SECP256K1_P:
        return None
    alpha = (pow(x, 3, _SECP256K1_P) + 7) % _SECP256K1_P
    beta = pow(alpha, (_SECP256K1_P + 1) // 4, _SECP256K1_P)
    if (beta & 1) != (odd & 1):
        beta = (-beta) % _SECP256K1_P
    return x, beta


def _recover_public_key(
    recid: int, digest: bytes, r: int, s: int
) -> Optional[tuple[int, int]]:
    if not (0 <= recid <= 3):
        return None
    if not (1 <= r < _SECP256K1_N and 1 <= s < _SECP256K1_N):
        return None
    x = r + (recid >> 1) * _SECP256K1_N
    R = _lift_x(x, recid & 1)
    if R is None:
        return None
    if _scalar_multiply(_SECP256K1_N, R) is not None:
        return None
    e = int.from_bytes(digest, "big") % _SECP256K1_N
    r_inv = _inverse_mod(r, _SECP256K1_N)
    sR = _scalar_multiply(s % _SECP256K1_N, R)
    eG = _scalar_multiply(e, _SECP256K1_G)
    pre_q = _point_sub(sR, eG)
    if pre_q is None:
        return None
    return _scalar_multiply(r_inv % _SECP256K1_N, pre_q)


def _point_to_bytes(point: tuple[int, int], compressed: bool) -> bytes:
    x, y = point
    if compressed:
        prefix = 0x03 if y & 1 else 0x02
        return bytes([prefix]) + x.to_bytes(32, "big")
    return b"\x04" + x.to_bytes(32, "big") + y.to_bytes(32, "big")


def pubkey_to_p2pkh_address(pubkey: tuple[int, int], compressed: bool) -> str:
    pub_bytes = _point_to_bytes(pubkey, compressed)
    sha = hashlib.sha256(pub_bytes).digest()
    ripe = hashlib.new("ripemd160", sha).digest()
    versioned = b"\x00" + ripe
    checksum = hashlib.sha256(hashlib.sha256(versioned).digest()).digest()[:4]
    return b58encode(versioned + checksum).decode("ascii")


def iter_signature_segments(signature: str) -> Iterable[str]:
    """Yield individual base64 signatures from a concatenated string."""

    for match in BASE64_SEGMENT_PATTERN.finditer(signature):
        yield match.group(0)


def verify_segments(address: str, message: str, signature: str) -> List[SignatureCheckResult]:
    """Verify each base64 segment for the provided address/message."""

    digest = bitcoin_message_hash(message)

    results: List[SignatureCheckResult] = []
    for idx, segment in enumerate(iter_signature_segments(signature), start=1):
        derived_address: Optional[str] = None
        try:
            raw = base64.b64decode(segment)
            if len(raw) != 65:
                raise ValueError("signature must decode to 65 bytes")
            header = raw[0]
            if header < 27 or header > 34:
                raise ValueError("header byte out of range")
            recid = header - 27
            compressed = False
            if recid >= 4:
                compressed = True
                recid -= 4
            r = int.from_bytes(raw[1:33], "big")
            s = int.from_bytes(raw[33:], "big")
            pub_point = _recover_public_key(recid, digest, r, s)
            if pub_point is None:
                raise ValueError("could not recover public key")
            derived_address = pubkey_to_p2pkh_address(pub_point, compressed)
            valid = derived_address == address
        except Exception:
            valid = False
        results.append(SignatureCheckResult(idx, segment, valid, derived_address))
    return results


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify Bitcoin puzzle message signatures.")
    parser.add_argument("--address", required=True, help="Bitcoin address that allegedly signed the message")
    parser.add_argument("--message", required=True, help="Exact message string that was signed")
    parser.add_argument("--signature", required=True, help="Concatenated base64 signature string")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return parser


def main() -> None:
    parser = build_cli()
    args = parser.parse_args()

    results = verify_segments(args.address, args.message, args.signature)
    payload = {
        "address": args.address,
        "message": args.message,
        "segments": [result.to_dict() for result in results],
        "valid_segment_count": sum(result.valid for result in results),
        "total_segments": len(results),
    }

    json_kwargs = {"ensure_ascii": False}
    if args.pretty:
        json_kwargs["indent"] = 2
    print(json.dumps(payload, **json_kwargs))


if __name__ == "__main__":
    main()
