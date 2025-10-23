from __future__ import annotations

import base64
import hashlib
import hmac

from verifier.verify_puzzle_signature import (
    PkScriptExpectation,
    _SECP256K1_G,
    _SECP256K1_N,
    _inverse_mod,
    _point_to_bytes,
    _scalar_multiply,
    bitcoin_message_hash,
    build_p2pk_script,
    hash160,
    pubkey_to_p2pkh_address,
    verify_segments,
)


def _deterministic_k(priv_key: int, digest: bytes) -> int:
    key = priv_key.to_bytes(32, "big")
    V = b"\x01" * 32
    K = b"\x00" * 32
    K = hmac.new(K, V + b"\x00" + key + digest, hashlib.sha256).digest()
    V = hmac.new(K, V, hashlib.sha256).digest()
    K = hmac.new(K, V + b"\x01" + key + digest, hashlib.sha256).digest()
    V = hmac.new(K, V, hashlib.sha256).digest()
    while True:
        V = hmac.new(K, V, hashlib.sha256).digest()
        candidate = int.from_bytes(V, "big")
        if 1 <= candidate < _SECP256K1_N:
            return candidate
        K = hmac.new(K, V + b"\x00", hashlib.sha256).digest()
        V = hmac.new(K, V, hashlib.sha256).digest()


def _sign_message(priv_key: int, message: str, compressed: bool) -> str:
    digest = bitcoin_message_hash(message)
    k = _deterministic_k(priv_key, digest)
    R = _scalar_multiply(k, _SECP256K1_G)
    assert R is not None
    r = R[0] % _SECP256K1_N
    s = (_inverse_mod(k, _SECP256K1_N) * (int.from_bytes(digest, "big") + r * priv_key)) % _SECP256K1_N
    recid = (2 if R[0] >= _SECP256K1_N else 0) | (R[1] & 1)
    if s > _SECP256K1_N // 2:
        s = _SECP256K1_N - s
        recid ^= 1
    header = 27 + recid + (4 if compressed else 0)
    signature_bytes = bytes([header]) + r.to_bytes(32, "big") + s.to_bytes(32, "big")
    return base64.b64encode(signature_bytes).decode("ascii")


def test_verify_segments_accepts_address_and_pkscript_targets() -> None:
    priv_key = 1
    message = "Echo verifier integration"
    pub_point = _scalar_multiply(priv_key, _SECP256K1_G)
    assert pub_point is not None

    compressed_signature = _sign_message(priv_key, message, compressed=True)
    address = pubkey_to_p2pkh_address(pub_point, compressed=True)

    address_results = verify_segments(address, message, compressed_signature)
    assert len(address_results) == 1
    assert address_results[0].valid is True
    assert address_results[0].derived_address == address
    assert address_results[0].derived_pubkey is None
    assert address_results[0].derived_pkscript is None

    uncompressed_bytes = _point_to_bytes(pub_point, False)
    pkscript_text = f"Pkscript\n{uncompressed_bytes.hex()}\nOP_CHECKSIG"
    uncompressed_signature = _sign_message(priv_key, message, compressed=False)

    pkscript_results = verify_segments(None, message, uncompressed_signature, pkscript_text)
    assert len(pkscript_results) == 1
    result = pkscript_results[0]
    assert result.valid is True
    assert result.derived_address is None
    assert result.derived_pubkey == uncompressed_bytes.hex()
    assert result.derived_pkscript == build_p2pk_script(uncompressed_bytes).hex()


def test_verify_segments_rejects_mismatched_pkscript() -> None:
    priv_key = 2
    message = "Echo verifier mismatch"
    pub_point = _scalar_multiply(priv_key, _SECP256K1_G)
    assert pub_point is not None

    signature = _sign_message(priv_key, message, compressed=False)
    wrong_point = _scalar_multiply(3, _SECP256K1_G)
    assert wrong_point is not None
    wrong_pub_bytes = _point_to_bytes(wrong_point, False)
    expectation = PkScriptExpectation(pubkey=wrong_pub_bytes, script=build_p2pk_script(wrong_pub_bytes))

    results = verify_segments(None, message, signature, expectation)
    assert len(results) == 1
    assert results[0].valid is False
    assert results[0].derived_pubkey == _point_to_bytes(pub_point, False).hex()


def test_verify_segments_accepts_p2sh_script_expectation() -> None:
    priv_key = 3
    message = "Echo verifier p2sh"
    pub_point = _scalar_multiply(priv_key, _SECP256K1_G)
    assert pub_point is not None

    compressed_signature = _sign_message(priv_key, message, compressed=True)
    compressed_bytes = _point_to_bytes(pub_point, True)
    redeem_script = build_p2pk_script(compressed_bytes)
    script_hash = hash160(redeem_script)
    script_text = "\n".join(
        [
            "3HyaLqxcf-umnCTgSE4",
            "Pkscript",
            "OP_HASH160",
            script_hash.hex(),
            "OP_EQUAL",
        ]
    )

    results = verify_segments(None, message, compressed_signature, script_text)
    assert len(results) == 1
    result = results[0]
    assert result.valid is True
    assert result.derived_pubkey == compressed_bytes.hex()
    expected_script = b"\xa9\x14" + script_hash + b"\x87"
    assert result.derived_pkscript == expected_script.hex()


def test_verify_segments_rejects_wrong_p2sh_script_hash() -> None:
    priv_key = 5
    message = "Echo verifier p2sh mismatch"
    pub_point = _scalar_multiply(priv_key, _SECP256K1_G)
    assert pub_point is not None

    signature = _sign_message(priv_key, message, compressed=False)
    script_text = "\n".join(
        [
            "Pkscript",
            "OP_HASH160",
            "00" * 20,
            "OP_EQUAL",
        ]
    )

    results = verify_segments(None, message, signature, script_text)
    assert len(results) == 1
    result = results[0]
    assert result.valid is False
    assert result.derived_pubkey == _point_to_bytes(pub_point, False).hex()
    derived_script = b"\xa9\x14" + hash160(build_p2pk_script(_point_to_bytes(pub_point, False))) + b"\x87"
    assert result.derived_pkscript == derived_script.hex()
