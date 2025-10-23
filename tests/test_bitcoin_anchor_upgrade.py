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
