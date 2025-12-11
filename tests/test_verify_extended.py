"""Behavioural tests for :mod:`verifier.verify_extended`.

The test dataset covers both legacy P2PKH addresses and Taproot addresses
that require bech32m checksums and x-only public keys.
"""

from __future__ import annotations

from pathlib import Path

import verifier.verify_extended as ve


def _bech32m_encode(hrp: str, version: int, program: bytes) -> str:
    data = [version] + ve._convertbits(program, 8, 5, pad=True)
    checksum = ve._bech32_create_checksum(hrp, data, encoding="bech32m")
    combined = data + checksum
    return hrp + "1" + "".join(ve._BECH32_ALPHABET[d] for d in combined)


def test_verify_dataset_accepts_p2pkh(tmp_path: Path) -> None:
    dataset = tmp_path / "pairs.csv"
    pubkey = "0279BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798"
    address = "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH"
    dataset.write_text(f"{address},{pubkey}\n", encoding="utf-8")

    results = ve.verify_dataset(str(dataset))

    assert len(results) == 1
    assert results[0].valid is True
    assert results[0].reason is None


def test_verify_dataset_accepts_taproot(tmp_path: Path) -> None:
    dataset = tmp_path / "taproot.csv"
    pubkey_bytes = bytes.fromhex(
        "03d6f8e12c72ded9a2ce8abec1bf6a55d1b355d98f6054293e345be7b69c1a0001"
    )
    xonly = pubkey_bytes[1:33]
    address = _bech32m_encode("bc", 1, xonly)
    dataset.write_text(f"{address},{pubkey_bytes.hex()}\n", encoding="utf-8")

    results = ve.verify_dataset(str(dataset))

    assert results[0].valid is True
    assert results[0].reason is None


def test_verify_dataset_rejects_wrong_taproot_encoding(tmp_path: Path) -> None:
    dataset = tmp_path / "bad.csv"
    pubkey_bytes = bytes.fromhex(
        "03d6f8e12c72ded9a2ce8abec1bf6a55d1b355d98f6054293e345be7b69c1a0001"
    )
    xonly = pubkey_bytes[1:33]
    # Force a bech32 checksum for a v1 witness program to trigger validation error.
    data = [1] + ve._convertbits(xonly, 8, 5, pad=True)
    checksum = ve._bech32_create_checksum("bc", data, encoding="bech32")
    address = "bc1" + "".join(ve._BECH32_ALPHABET[d] for d in data + checksum)
    dataset.write_text(f"{address},{pubkey_bytes.hex()}\n", encoding="utf-8")

    results = ve.verify_dataset(str(dataset))

    assert results[0].valid is False
    assert "bech32m" in (results[0].reason or "")
