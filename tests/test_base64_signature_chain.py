"""Tests for :mod:`tools.base64_signature_chain`."""

from __future__ import annotations

import base64
import hashlib

import pytest

from tools.base64_signature_chain import SignatureChain, SignatureFormatError


def _expected_attestation(chunks: list[str]) -> str:
    from tools.base64_signature_chain import _base58check_encode  # type: ignore[attr-defined]

    decoded = [base64.b64decode(chunk, validate=True) for chunk in chunks]
    digest = hashlib.sha256(b"".join(decoded)).digest()
    ripemd = hashlib.new("ripemd160", digest).digest()
    return _base58check_encode(b"\x00" + ripemd)


def test_attestation_address_matches_bitcoin_style_hashing() -> None:
    fragments = [
        base64.b64encode(b"Echo").decode(),
        base64.b64encode(b"Sovereign Cipher").decode(),
    ]
    chain = SignatureChain(entries=fragments)

    assert chain.attestation_address() == _expected_attestation(fragments)


def test_attestation_address_rejects_empty_chain() -> None:
    chain = SignatureChain(entries=[])

    with pytest.raises(ValueError):
        chain.attestation_address()


def test_attestation_address_surfaces_invalid_base64() -> None:
    chain = SignatureChain(entries=["not-base64!!"])

    with pytest.raises(SignatureFormatError):
        chain.attestation_address()
