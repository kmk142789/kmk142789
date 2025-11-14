from __future__ import annotations

import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from tools import verify_claims


@pytest.fixture()
def example_private_key() -> ec.EllipticCurvePrivateKey:
    # Deterministic key derived from fixed integer for repeatable tests.
    return ec.derive_private_key(1_234_567_890_123_456_789_012_345_678_901, ec.SECP256K1())


def _pubkey_hex_from_private_key(private_key: ec.EllipticCurvePrivateKey) -> str:
    public_numbers = private_key.public_key().public_numbers()
    return f"{public_numbers.x:064x}{public_numbers.y:064x}"


def _write_claim(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_verify_claim_accepts_valid_ecdsa(tmp_path: Path, example_private_key: ec.EllipticCurvePrivateKey) -> None:
    canonical = "EchoEvolver affirms sovereign intent."
    signature = example_private_key.sign(canonical.encode(), ec.ECDSA(hashes.SHA256()))
    claim = {
        "canonical": canonical,
        "signature": {
            "algo": "ecdsa-secp256k1",
            "pub": _pubkey_hex_from_private_key(example_private_key),
            "sig": signature.hex(),
        },
    }
    claim_path = _write_claim(tmp_path / "claim.json", claim)

    assert verify_claims.verify_claim(claim_path)


def test_verify_claim_rejects_bad_signature(tmp_path: Path, example_private_key: ec.EllipticCurvePrivateKey) -> None:
    canonical = "EchoEvolver orbits the void."
    signature = example_private_key.sign(b"something else", ec.ECDSA(hashes.SHA256()))
    claim = {
        "canonical": canonical,
        "signature": {
            "algo": "ecdsa-secp256k1",
            "pub": _pubkey_hex_from_private_key(example_private_key),
            "sig": signature.hex(),
        },
    }
    claim_path = _write_claim(tmp_path / "claim.json", claim)

    assert not verify_claims.verify_claim(claim_path)


def test_verify_claim_reports_hmac_claim(tmp_path: Path) -> None:
    claim = {
        "canonical": "EchoEvolver cycles remain private.",
        "signature": {
            "algo": "hmac-sha256",
            "sig": "deadbeef",
        },
    }
    claim_path = _write_claim(tmp_path / "claim.json", claim)

    assert verify_claims.verify_claim(claim_path)
