"""Utilities for reproducing the Satoshi Puzzle #3 solution.

This module implements a tiny subset of the secp256k1 elliptic curve
arithmetic that is required to regenerate the public information for the
address ``19ZewH8Kk1PDbSNdJ97FP4EiCjTRaZMZQA``.

The original puzzle challenged participants to recover the private key that
produces the Pay-to-PubKey-Hash script provided in the puzzle description. The
solution is the tiny integer ``7``; everything else in the puzzle (the public
key, the hash160 fingerprint, and the base58check-encoded P2PKH address) can be
re-derived deterministically from that secret.

The functions below are deliberately self-contained so that the derivation can
be reproduced without relying on external cryptography libraries.  The goal is
not to provide a full featured Bitcoin toolkit, merely a small, easy to audit
reference implementation that demonstrates the mathematics involved.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict

# --- Elliptic curve parameters (secp256k1) ---------------------------------

_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_GX = 55066263022277343669578718895168534326250603453777594175500187360389116729240
_GY = 32670510020758816978083085130507043184471273380659243275938904335757337482424


@dataclass(frozen=True)
class _Point:
    """Affine point on the secp256k1 curve."""

    x: int | None
    y: int | None

    @property
    def is_infinity(self) -> bool:
        return self.x is None or self.y is None


_INFINITY = _Point(None, None)
_GENERATOR = _Point(_GX, _GY)


# --- Helper utilities ------------------------------------------------------

def _inverse_mod(k: int, p: int = _P) -> int:
    """Return the modular multiplicative inverse of ``k`` mod ``p``."""

    if k % p == 0:
        raise ZeroDivisionError("Inverse does not exist")
    return pow(k, p - 2, p)


def _point_add(p1: _Point, p2: _Point) -> _Point:
    """Add two points on the elliptic curve."""

    if p1.is_infinity:
        return p2
    if p2.is_infinity:
        return p1

    if p1.x == p2.x and (p1.y != p2.y or p1.y == 0):
        return _INFINITY

    if p1 == p2:
        m = (3 * p1.x * p1.x) * _inverse_mod(2 * p1.y, _P)
    else:
        m = (p2.y - p1.y) * _inverse_mod((p2.x - p1.x) % _P, _P)

    m %= _P
    x3 = (m * m - p1.x - p2.x) % _P
    y3 = (m * (p1.x - x3) - p1.y) % _P
    return _Point(x3, y3)


def _scalar_multiply(k: int, point: _Point = _GENERATOR) -> _Point:
    """Multiply ``point`` by the integer ``k`` using the double-and-add method."""

    if k % _N == 0 or point.is_infinity:
        return _INFINITY

    result = _INFINITY
    addend = point
    remaining = k

    while remaining:
        if remaining & 1:
            result = _point_add(result, addend)
        addend = _point_add(addend, addend)
        remaining >>= 1

    return result


# --- Encoding helpers ------------------------------------------------------

_BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _base58check_encode(payload: bytes) -> str:
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    full_payload = payload + checksum

    num = int.from_bytes(full_payload, "big")
    result = ""
    while num > 0:
        num, remainder = divmod(num, 58)
        result = _BASE58_ALPHABET[remainder] + result

    # Preserve leading zero bytes as alphabet's first character.
    leading_zero_bytes = len(full_payload) - len(full_payload.lstrip(b"\x00"))
    return "1" * leading_zero_bytes + result


def _hash160(data: bytes) -> bytes:
    sha = hashlib.sha256(data).digest()
    ripemd = hashlib.new("ripemd160", sha).digest()
    return ripemd


# --- Public API ------------------------------------------------------------

def derive_puzzle3_solution() -> Dict[str, str]:
    """Return the canonical data for Satoshi's Puzzle #3.

    The dictionary contains human-readable hex strings for the public
    information along with the decimal private key for convenience.
    """

    private_key = 7
    point = _scalar_multiply(private_key)
    if point.is_infinity:
        raise RuntimeError("Failed to derive public key from private key")

    prefix = b"\x02" if point.y % 2 == 0 else b"\x03"
    compressed_public_key = prefix + point.x.to_bytes(32, "big")

    h160 = _hash160(compressed_public_key)
    address_payload = b"\x00" + h160
    address = _base58check_encode(address_payload)

    script = " ".join(
        [
            "OP_DUP",
            "OP_HASH160",
            h160.hex(),
            "OP_EQUALVERIFY",
            "OP_CHECKSIG",
        ]
    )

    return {
        "private_key_decimal": str(private_key),
        "private_key_hex": f"{private_key:02x}",
        "public_key_compressed": compressed_public_key.hex(),
        "hash160": h160.hex(),
        "address": address,
        "pkscript": script,
    }


__all__ = ["derive_puzzle3_solution"]
