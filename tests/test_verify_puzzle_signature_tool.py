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
    parse_pkscript,
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


def test_parse_pkscript_allows_split_op_check_sig() -> None:
    priv_key = 3
    pub_point = _scalar_multiply(priv_key, _SECP256K1_G)
    assert pub_point is not None

    uncompressed_bytes = _point_to_bytes(pub_point, False)
    script_text = f"Pkscript\n{uncompressed_bytes.hex()}\nOP_CHECK\nSIG"

    expectation = parse_pkscript(script_text)

    assert expectation.pubkey == uncompressed_bytes
    assert expectation.script == build_p2pk_script(uncompressed_bytes)


def test_parse_pkscript_allows_fragmented_op_checksig() -> None:
    priv_key = 5
    pub_point = _scalar_multiply(priv_key, _SECP256K1_G)
    assert pub_point is not None

    uncompressed_bytes = _point_to_bytes(pub_point, False)
    script_text = f"Pkscript\n{uncompressed_bytes.hex()}\nOP_CH\nECKSIG"

    expectation = parse_pkscript(script_text)

    assert expectation.pubkey == uncompressed_bytes
    assert expectation.script == build_p2pk_script(uncompressed_bytes)


def test_parse_pkscript_ignores_leading_address_line() -> None:
    priv_key = 4
    pub_point = _scalar_multiply(priv_key, _SECP256K1_G)
    assert pub_point is not None

    uncompressed_bytes = _point_to_bytes(pub_point, False)
    address = pubkey_to_p2pkh_address(pub_point, compressed=False)
    address_with_dash = address[:6] + "-" + address[6:]

    script_text = (
        f"{address_with_dash}\nPkscript\n{uncompressed_bytes.hex()}\nOP_CHECKSIG"
    )

    expectation = parse_pkscript(script_text)

    assert expectation.pubkey == uncompressed_bytes
    assert expectation.script == build_p2pk_script(uncompressed_bytes)
