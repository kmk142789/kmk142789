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
from typing import Iterable, List, Optional, Union

from .pkscript_registry import canonicalise_tokens

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
    derived_pubkey: Optional[str] = None
    derived_pkscript: Optional[str] = None

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "signature": self.signature,
            "valid": self.valid,
            "derived_address": self.derived_address,
            "derived_pubkey": self.derived_pubkey,
            "derived_pkscript": self.derived_pkscript,
        }


@dataclass
class PkScriptExpectation:
    """Canonical representation of the expected pay-to-pubkey script."""

    pubkey: bytes
    script: bytes

    @property
    def pubkey_hex(self) -> str:
        return self.pubkey.hex()

    @property
    def script_hex(self) -> str:
        return self.script.hex()


BASE64_SEGMENT_PATTERN = re.compile(r"[A-Za-z0-9+/]+={0,2}")

BASE58_ALPHABET = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

HEX_TOKEN_PATTERN = re.compile(r"^[0-9a-fA-F]+$")
IGNORED_PK_TOKENS = {"PKSCRIPT"}


def _looks_like_base58(value: str) -> bool:
    """Return True if the token resembles a Base58 string (optionally dashed)."""

    if not value:
        return False
    cleaned = value.replace("-", "")
    if not cleaned:
        return False
    try:
        candidate = cleaned.encode("ascii")
    except UnicodeEncodeError:
        return False
    return all(byte in BASE58_ALPHABET for byte in candidate)


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


def build_p2pk_script(pubkey: bytes) -> bytes:
    return bytes([len(pubkey)]) + pubkey + b"\xac"


def parse_pkscript(value: str) -> PkScriptExpectation:
    """Parse a textual pay-to-pubkey script description."""

    cleaned = value.replace(":", " ").replace(",", " ")
    tokens = canonicalise_tokens(cleaned.split())

    hex_parts: list[str] = []
    saw_op_checksig = False
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        if not token:
            idx += 1
            continue
        upper = token.upper()
        if upper == "OP_CHECKSIG":
            saw_op_checksig = True
            idx += 1
            continue
        if upper == "OP_CHECK" and idx + 1 < len(tokens):
            next_token = tokens[idx + 1].upper()
            if next_token in {"SIG"}:
                saw_op_checksig = True
                idx += 2
                continue
        if upper in IGNORED_PK_TOKENS:
            idx += 1
            continue
        if upper.startswith("0X"):
            token = token[2:]
            upper = token.upper()
        if not HEX_TOKEN_PATTERN.fullmatch(token):
            if not hex_parts and _looks_like_base58(token):
                idx += 1
                continue
            raise ValueError(f"invalid token {token!r} in pk script")
        hex_parts.append(token)
        idx += 1

    if not hex_parts and not saw_op_checksig:
        raise ValueError("pk script must contain public key hex data")

    hex_data = "".join(hex_parts)
    if hex_data and len(hex_data) % 2 != 0:
        raise ValueError("pk script hex data must have an even length")

    script_bytes = bytes.fromhex(hex_data) if hex_data else b""
    if saw_op_checksig and (not script_bytes or script_bytes[-1] != 0xAC):
        script_bytes += b"\xac"

    if not script_bytes:
        raise ValueError("pk script contains no data")

    payload = script_bytes
    if payload[-1] == 0xAC:
        payload = payload[:-1]

    if not payload:
        raise ValueError("pk script missing public key bytes")

    if payload[0] in (0x21, 0x41) and len(payload) > 1:
        length = payload[0]
        if len(payload) - 1 != length:
            raise ValueError("pk script pushdata length mismatch")
        pubkey = payload[1:]
    else:
        pubkey = payload

    if len(pubkey) == 33:
        if pubkey[0] not in (0x02, 0x03):
            raise ValueError("compressed public key must start with 0x02 or 0x03")
    elif len(pubkey) == 65:
        if pubkey[0] != 0x04:
            raise ValueError("uncompressed public key must start with 0x04")
    else:
        raise ValueError("public key must be 33 or 65 bytes long")

    return PkScriptExpectation(pubkey=pubkey, script=build_p2pk_script(pubkey))


def iter_signature_segments(signature: str) -> Iterable[str]:
    """Yield individual base64 signatures from a concatenated string."""

    for match in BASE64_SEGMENT_PATTERN.finditer(signature):
        yield match.group(0)


def verify_segments(
    address: Optional[str],
    message: str,
    signature: str,
    pkscript: Optional[Union[str, PkScriptExpectation]] = None,
) -> List[SignatureCheckResult]:
    """Verify each base64 segment for the provided address/message."""

    expectation: Optional[PkScriptExpectation]
    if isinstance(pkscript, str):
        expectation = parse_pkscript(pkscript)
    else:
        expectation = pkscript

    if (address is None) == (expectation is None):
        raise ValueError("must provide exactly one of address or pk script")

    digest = bitcoin_message_hash(message)

    results: List[SignatureCheckResult] = []
    for idx, segment in enumerate(iter_signature_segments(signature), start=1):
        derived_address: Optional[str] = None
        derived_pubkey_hex: Optional[str] = None
        derived_pkscript_hex: Optional[str] = None
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

            if expectation is None:
                derived_address = pubkey_to_p2pkh_address(pub_point, compressed)
                valid = derived_address == address
            else:
                chosen = _point_to_bytes(pub_point, compressed)
                derived_pubkey_hex = chosen.hex()
                derived_pkscript_hex = build_p2pk_script(chosen).hex()

                uncompressed = _point_to_bytes(pub_point, False)
                compressed_bytes = _point_to_bytes(pub_point, True)
                if expectation.pubkey == uncompressed:
                    derived_pubkey_hex = uncompressed.hex()
                    derived_pkscript_hex = build_p2pk_script(uncompressed).hex()
                    valid = True
                elif expectation.pubkey == compressed_bytes:
                    derived_pubkey_hex = compressed_bytes.hex()
                    derived_pkscript_hex = build_p2pk_script(compressed_bytes).hex()
                    valid = True
                else:
                    valid = False
        except Exception:
            valid = False

        results.append(
            SignatureCheckResult(
                idx,
                segment,
                valid,
                derived_address,
                derived_pubkey_hex,
                derived_pkscript_hex,
            )
        )
    return results


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify Bitcoin puzzle message signatures.")
    parser.add_argument(
        "--address",
        help="Bitcoin address that allegedly signed the message",
    )
    parser.add_argument(
        "--pkscript",
        help=(
            "Expected pay-to-pubkey script. Accepts hex with optional OP_CHECKSIG token "
            "or labelled multi-line text."
        ),
    )
    parser.add_argument("--message", required=True, help="Exact message string that was signed")
    parser.add_argument("--signature", required=True, help="Concatenated base64 signature string")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return parser


def main() -> None:
    parser = build_cli()
    args = parser.parse_args()

    if (args.address is None) == (args.pkscript is None):
        parser.error("provide exactly one of --address or --pkscript")

    script_expectation: Optional[PkScriptExpectation] = None
    if args.pkscript is not None:
        try:
            script_expectation = parse_pkscript(args.pkscript)
        except ValueError as exc:
            parser.error(f"invalid --pkscript value: {exc}")

    results = verify_segments(
        args.address,
        args.message,
        args.signature,
        script_expectation,
    )
    payload = {
        "message": args.message,
        "segments": [result.to_dict() for result in results],
        "valid_segment_count": sum(result.valid for result in results),
        "total_segments": len(results),
    }

    if args.address is not None:
        payload["address"] = args.address
    if script_expectation is not None:
        payload["pkscript"] = script_expectation.script_hex
        payload["pubkey"] = script_expectation.pubkey_hex

    json_kwargs = {"ensure_ascii": False}
    if args.pretty:
        json_kwargs["indent"] = 2
    print(json.dumps(payload, **json_kwargs))


if __name__ == "__main__":
    main()
