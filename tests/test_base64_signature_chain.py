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


def test_from_blob_parses_concatenated_segments():
    blob = (
        "IBkKehJLiV+3cKg/dFiBRunBTnK52+PkmAr7Jn3C+1Z9V2bhCCKN4XzQBGedcL8I"
        "7B8hyNXjKpI6+viaPAVmIHc=ICS7U+ErcA7ZDy5sJRKCeWIK/+WcqDASRzC/qNQ3L"
        "4QRNL8gh2r5MG2fqtdOoFmaqiLX01lh7YMedYj5Afaus3Q=IALY2kh66PPSgfcdUn"
        "f7nOj+vtlQW4dfi0HUriXpde4SA21cr6JtXjDaQCv6WN+SzWpu75T20GhNPTwQtJ6"
        "AmWg=H2mCXlYiwjO3pI/eCicVo0VVb7WNLzemH7JrdazeblFoLKorgUEl9Cg4qAZkz"
        "KjX5IvWFojF/UkLVMcGpP2l/os=H0JIM7qFZpDTWIUTz20J3BLdTmqeiFB78btpzc0"
        "QoO6nf7SI6EPdHA6x2m/+y1qsgDhCXmm/oJphcQYFxLmdRtw=H3VAhmNKBwLDsqf8D"
        "Ky3cr+DfL3AD/20uVt5wYU9oh7sFngEK3dhtLq6cOXZhtFxUxgt2BItuWsLMgGZ+iK"
        "xurU="
    )

    chain = SignatureChain.from_blob(blob)

    assert len(chain.entries) == 6
    chain.validate()  # should not raise
    assert chain.blob == blob


def test_from_blob_handles_whitespace_delimited_input():
    entries = [
        "ABCDEF==",
        "GhIJKL==",
        "mnopqr==",
    ]
    blob = "\n".join(entries)

    chain = SignatureChain.from_blob(blob)

    assert chain.entries == entries
    assert chain.blob.replace("\n", "") == "".join(entries)
