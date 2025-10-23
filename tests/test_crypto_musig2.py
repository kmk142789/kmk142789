"""Unit tests for the :mod:`crypto.musig2` helper utilities."""

from __future__ import annotations

import pytest

from echo.crypto.musig2 import (
    MuSig2Error,
    MuSig2Session,
    compute_partial_signature,
    derive_xonly_public_key,
    generate_nonce,
    schnorr_verify,
)


def _make_signers(count: int = 2) -> tuple[list[int], list[bytes]]:
    secrets = [int.to_bytes(index + 1, 32, "big") for index in range(count)]
    scalars: list[int] = []
    pubkeys: list[bytes] = []
    for secret in secrets:
        scalar, pubkey = derive_xonly_public_key(secret)
        scalars.append(scalar)
        pubkeys.append(pubkey)
    return scalars, pubkeys


def test_musig2_session_roundtrip_signature() -> None:
    scalars, pubkeys = _make_signers(2)
    message = b"MuSig2 roundtrip"
    session = MuSig2Session.create(pubkeys, message)

    nonce_scalars: dict[str, int] = {}
    for index, scalar in enumerate(scalars, start=1):
        entropy = int.to_bytes(index, 32, "big")
        nonce_scalar, nonce_pub = generate_nonce(scalar, entropy, message)
        participant = pubkeys[index - 1].hex()
        session.register_nonce(participant, nonce_pub)
        nonce_scalars[participant] = nonce_scalar

    assert session.aggregated_nonce is not None

    for scalar, pubkey in zip(scalars, pubkeys):
        participant = pubkey.hex()
        partial = compute_partial_signature(session, participant, scalar, nonce_scalars[participant])
        session.add_partial_signature(participant, partial)

    signature = session.final_signature()
    assert schnorr_verify(session.aggregated_public_key, message, signature)

    exported = session.to_dict()
    restored = MuSig2Session.from_dict(exported)
    assert restored.aggregated_public_key == session.aggregated_public_key
    assert restored.final_signature() == signature


def test_generate_nonce_requires_entropy() -> None:
    with pytest.raises(MuSig2Error):
        generate_nonce(5, b"short", b"entropy check")


def test_register_nonce_unknown_participant() -> None:
    scalars, pubkeys = _make_signers(1)
    session = MuSig2Session.create(pubkeys, b"orphan nonce")
    with pytest.raises(MuSig2Error):
        session.register_nonce("deadbeef", b"\x01" * 32)


def test_partial_signature_requires_nonce() -> None:
    scalars, pubkeys = _make_signers(1)
    session = MuSig2Session.create(pubkeys, b"pending")
    with pytest.raises(MuSig2Error):
        compute_partial_signature(session, pubkeys[0].hex(), scalars[0], 1)
