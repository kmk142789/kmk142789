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
from typing import Iterable, List

from coincurve import PublicKey


@dataclass
class SignatureCheckResult:
    """Result for a single signature segment."""

    index: int
    signature: str
    valid: bool

    def to_dict(self) -> dict[str, object]:
        return {"index": self.index, "signature": self.signature, "valid": self.valid}


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


def pubkey_to_p2pkh_address(pubkey: PublicKey, compressed: bool) -> str:
    pub_bytes = pubkey.format(compressed)
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
            recoverable = bytes([recid]) + raw[1:]
            pub = PublicKey.from_signature_and_digest(recoverable, digest)
            derived_address = pubkey_to_p2pkh_address(pub, compressed)
            valid = derived_address == address
        except Exception:
            valid = False
        results.append(SignatureCheckResult(idx, segment, valid))
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
