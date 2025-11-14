"""Utilities for working with the Bitcoin Base58 alphabet.

The repository already shipped several helpers that duplicated portions of
this logic for CLI tools.  The BIP32 parser requires both encoding and
decoding routines with checksum validation, so this module centralises the
behaviour.
"""

from __future__ import annotations

from hashlib import sha256

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


class Base58Error(ValueError):
    """Raised when Base58 encoding/decoding encounters invalid input."""


def _double_sha256(data: bytes) -> bytes:
    return sha256(sha256(data).digest()).digest()


def b58encode(data: bytes) -> str:
    """Encode *data* using the Bitcoin Base58 alphabet."""

    leading_zeros = 0
    for byte in data:
        if byte == 0:
            leading_zeros += 1
        else:
            break

    value = int.from_bytes(data, byteorder="big")
    encoded = ""
    while value:
        value, remainder = divmod(value, 58)
        encoded = BASE58_ALPHABET[remainder] + encoded

    if not encoded:
        encoded = "1" if data else ""

    return "1" * leading_zeros + encoded


def b58decode(data: str) -> bytes:
    """Decode a Base58 string back into raw bytes."""

    value = 0
    for char in data:
        try:
            index = BASE58_ALPHABET.index(char)
        except ValueError as exc:  # pragma: no cover - ValueError includes context
            raise Base58Error(f"Invalid Base58 character '{char}'") from exc
        value = value * 58 + index

    if value == 0:
        decoded = b""
    else:
        decoded = value.to_bytes((value.bit_length() + 7) // 8, byteorder="big")

    leading_zeros = 0
    for char in data:
        if char == "1":
            leading_zeros += 1
        else:
            break

    return b"\x00" * leading_zeros + decoded


def b58check_decode(data: str) -> bytes:
    """Decode a Base58Check string and verify the checksum."""

    decoded = b58decode(data)
    if len(decoded) < 4:
        raise Base58Error("Base58Check payload must be at least 4 bytes")

    payload, checksum = decoded[:-4], decoded[-4:]
    expected = _double_sha256(payload)[:4]
    if checksum != expected:
        raise Base58Error("Invalid Base58Check checksum")
    return payload


def b58check_encode(data: bytes) -> str:
    """Encode raw bytes with a Base58Check checksum."""

    checksum = _double_sha256(data)[:4]
    return b58encode(data + checksum)


__all__ = [
    "BASE58_ALPHABET",
    "Base58Error",
    "b58check_decode",
    "b58check_encode",
    "b58decode",
    "b58encode",
]
