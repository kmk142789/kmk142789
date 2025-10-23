"""Tests for :meth:`echo.evolver.EchoEvolver.upgrade_bitcoin_anchor_evidence`."""

from __future__ import annotations

import random

from echo.evolver import EchoEvolver


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
