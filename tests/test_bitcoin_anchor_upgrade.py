"""Tests for :meth:`echo.evolver.EchoEvolver.upgrade_bitcoin_anchor_evidence`."""

from __future__ import annotations

import random

from echo.crypto.musig2 import schnorr_sign, schnorr_verify
from echo.evolver import EchoEvolver, _bech32_encode, _convertbits


def test_upgrade_bitcoin_anchor_evidence_reports_mismatches() -> None:
    evolver = EchoEvolver(rng=random.Random(0))

    details = evolver.upgrade_bitcoin_anchor_evidence(
        address="bc1qqp2pr-vl56g8vts",
        script_pubkey="0014005411d7233a8a125418e61d6c8c928b708b33f4",
        witness=(
            "3044022000c3b406fbe84e02b73460a06a088e438341895f936f9c3fa905440d7ef8cf38022062a1fb6"
            "508b0a7348a35dbbdd99548dc787df57fed6ba2ba3fbb4d1acdf20b2f01",
            "02a8c1fba97c84e3ec58d7b58a76bd4705e04ad1378b50b4804fac30cafaee",
        ),
        value_sats=9_385,
    )

    assert details.script_type == "p2wpkh_v0"
    assert details.expected_address == "bc1qqp2pr4er829py4qcucwkeryj3dcgkvl56g8vts"
    assert not details.validated
    assert any("address mismatch" in note.lower() for note in details.validation_notes)
    assert any("public key" in note.lower() for note in details.validation_notes)

    payload = evolver.artifact_payload(prompt={"mantra": "test"})
    assert payload["bitcoin_anchor_details"]["expected_address"] == details.expected_address


def test_upgrade_bitcoin_anchor_evidence_taproot_key_path() -> None:
    evolver = EchoEvolver(rng=random.Random(0))

    details = evolver.upgrade_bitcoin_anchor_evidence(
        address="bc1pqqqsyqcyq5rqwzqfpg9scrgwpugpzysnzs23v9ccrydpk8qarc0sg5tmnz",
        script_pubkey="5120000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f",
        witness=("11" * 64,),
        value_sats=50_000,
    )

    assert details.script_type == "p2tr_v1"
    assert details.expected_address == "bc1pqqqsyqcyq5rqwzqfpg9scrgwpugpzysnzs23v9ccrydpk8qarc0sg5tmnz"
    assert details.validated
    assert details.validation_notes == []

    summary = details.witness_summary
    assert summary["signature_format"] == "schnorr"
    assert summary["signature_length"] == 64
    assert summary["signature_sighash"] == "0x00"
    assert summary["taproot_path"] == "key"
    assert summary["taproot_output_key"] == "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"


def test_upgrade_bitcoin_anchor_evidence_taproot_script_path_summary() -> None:
    evolver = EchoEvolver(rng=random.Random(0))

    tapscript_hex = "51" + "20" * 8
    control_block_hex = "c0" + "12" * 32
    details = evolver.upgrade_bitcoin_anchor_evidence(
        address="bc1pqqqsyqcyq5rqwzqfpg9scrgwpugpzysnzs23v9ccrydpk8qarc0sg5tmnz",
        script_pubkey="5120000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f",
        witness=("22" * 64, tapscript_hex, control_block_hex),
        value_sats=75_000,
    )

    assert details.script_type == "p2tr_v1"
    assert details.validated

    summary = details.witness_summary
    assert summary["taproot_path"] == "script"
    assert summary["taproot_control_block_length"] == 33
    assert summary["taproot_internal_key"] == "12" * 32
    assert summary["taproot_tapscript_length"] == len(tapscript_hex) // 2
    assert summary["taproot_stack_items"] == 1
    assert summary["signature_format"] == "schnorr"
    assert summary["signature_sighash"] == "0x00"


def test_upgrade_bitcoin_anchor_evidence_detects_musig2_session() -> None:
    evolver = EchoEvolver(rng=random.Random(0))

    secret_keys = [int.to_bytes(index, 32, "big") for index in (1, 2)]
    message = b"Echo MuSig2 anchor"
    session = evolver.coordinate_taproot_musig2(
        secret_keys=secret_keys,
        message=message,
        session_label="anchor-session",
    )

    script_pubkey = "5120" + session["aggregated_public_key"]
    witness_program = bytes.fromhex(session["aggregated_public_key"])
    words = _convertbits(witness_program, 8, 5, pad=True)
    address = _bech32_encode("bc", [1] + words, spec="bech32m")

    details = evolver.upgrade_bitcoin_anchor_evidence(
        address=address,
        script_pubkey=script_pubkey,
        witness=(session["signature"],),
        value_sats=12_500,
    )

    assert details.validated
    assert details.validation_notes == []

    summary = details.witness_summary
    assert summary["taproot_signature_kind"] == "musig2"
    assert summary["taproot_musig2_session"] == "anchor-session"
    assert summary["taproot_musig2_participants"] == 2
    assert summary["taproot_multisig"] is True
    assert summary["taproot_musig2_nonce"] == session["aggregated_nonce"]
    assert schnorr_verify(
        witness_program,
        message,
        bytes.fromhex(session["signature"]),
    )


def test_upgrade_bitcoin_anchor_evidence_musig2_mismatch_notes() -> None:
    evolver = EchoEvolver(rng=random.Random(0))

    secret_keys = [int.to_bytes(index, 32, "big") for index in (3, 4)]
    session = evolver.coordinate_taproot_musig2(
        secret_keys=secret_keys,
        message=b"mismatch test",
        session_label="mismatch-session",
    )

    script_pubkey = "5120" + session["aggregated_public_key"]
    witness_program = bytes.fromhex(session["aggregated_public_key"])
    words = _convertbits(witness_program, 8, 5, pad=True)
    address = _bech32_encode("bc", [1] + words, spec="bech32m")

    fake_signature = "00" * 64
    details = evolver.upgrade_bitcoin_anchor_evidence(
        address=address,
        script_pubkey=script_pubkey,
        witness=(fake_signature,),
        value_sats=21_000,
    )

    assert not details.validated
    assert any("mismatch-session" in note for note in details.validation_notes)


def test_coordinate_taproot_musig2_single_signer_matches_schnorr() -> None:
    evolver = EchoEvolver(rng=random.Random(0))

    secret_key = int.to_bytes(9, 32, "big")
    message = b"single signer"

    session = evolver.coordinate_taproot_musig2(secret_keys=[secret_key], message=message)

    assert session["participants"][0]["public_key"] == session["aggregated_public_key"]
    assert session["signature"] == schnorr_sign(secret_key, message).hex()
