from __future__ import annotations

import os

import pytest

from packages.core.src.echo.crypto.base58 import b58check_encode
from packages.core.src.echo.crypto.bip32_keys import ExtendedKey, ExtendedKeyError


def _build_extended_key(
    *,
    version: int,
    depth: int = 1,
    fingerprint: bytes | None = None,
    child_index: int = 1,
    chain_code: bytes | None = None,
    key_material: bytes,
) -> str:
    fingerprint = fingerprint or os.urandom(4)
    chain_code = chain_code or os.urandom(32)
    payload = b"".join(
        [
            version.to_bytes(4, "big"),
            depth.to_bytes(1, "big"),
            fingerprint,
            child_index.to_bytes(4, "big"),
            chain_code,
            key_material,
        ]
    )
    return b58check_encode(payload)


def test_decode_private_extended_key() -> None:
    key_material = b"\x00" + b"\x11" * 32
    encoded = _build_extended_key(version=0x0488ADE4, key_material=key_material)

    record = ExtendedKey.from_string(encoded)

    assert record.is_private is True
    assert record.version_info.coin == "bitcoin"
    assert record.version_info.network == "mainnet"
    assert record.depth == 1
    assert record.key_bytes == b"\x11" * 32


def test_decode_public_extended_key() -> None:
    public_key = b"\x02" + b"\x22" * 32
    encoded = _build_extended_key(version=0x02FACAFD, key_material=public_key)

    record = ExtendedKey.from_string(encoded)

    assert record.is_private is False
    assert record.version_info.coin == "dogecoin"
    assert record.version_info.network == "mainnet"
    assert record.key_bytes == public_key


def test_invalid_version() -> None:
    key_material = b"\x00" + b"\x33" * 32
    encoded = _build_extended_key(version=0xdeadbeef, key_material=key_material)

    with pytest.raises(ExtendedKeyError):
        ExtendedKey.from_string(encoded)


def test_invalid_checksum() -> None:
    key_material = b"\x02" + b"\x44" * 32
    encoded = _build_extended_key(version=0x0488B21E, key_material=key_material)
    tampered = encoded[:-1] + ("1" if encoded[-1] != "1" else "2")

    with pytest.raises(ExtendedKeyError):
        ExtendedKey.from_string(tampered)


def test_public_key_requires_compressed_point() -> None:
    key_material = b"\x04" + b"\x55" * 32
    encoded = _build_extended_key(version=0x0488B21E, key_material=key_material)

    with pytest.raises(ExtendedKeyError):
        ExtendedKey.from_string(encoded)


def test_private_key_requires_padding() -> None:
    key_material = b"\xFF" * 33
    encoded = _build_extended_key(version=0x0488ADE4, key_material=key_material)

    with pytest.raises(ExtendedKeyError):
        ExtendedKey.from_string(encoded)
