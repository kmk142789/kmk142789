from __future__ import annotations

import json
from pathlib import Path

import codex


FIXED_TIME = "2025-05-11T00:00:00+00:00"


def test_build_atlas_attestation_records_wallet_metadata() -> None:
    attestation = codex.build_atlas_attestation(
        project="Continuum Atlas",
        owner="Josh+Echo",
        xpub="xpub6CMHQ9GybwBEXAMPLEKEYXPm4o9saiN",
        fingerprint="61f21543",
        derivation_path="m/44h/0h/0h",
        signer="Josh+Echo",
        issued_at=FIXED_TIME,
    )

    wallets = attestation["ledger"]["wallets"]
    assert "61f21543" in wallets
    wallet_entry = wallets["61f21543"]
    assert wallet_entry["owner"] == "Josh+Echo"
    assert wallet_entry["metadata"]["derivation_path"] == "m/44h/0h/0h"
    assert wallet_entry["metadata"]["extended_public_key"].startswith("xpub6CMHQ9GybwBE")

    summary = attestation["compass_summary"]
    assert summary[0].startswith("Continuum Compass :: Continuum Atlas")
    assert attestation["signature"]


def test_codex_attest_cli_writes_json(monkeypatch, tmp_path: Path) -> None:
    export_path = tmp_path / "wallet-attest.json"
    monkeypatch.setattr(codex, "_current_timestamp", lambda: FIXED_TIME)

    exit_code = codex.main(
        [
            "attest",
            "--project",
            "Continuum Atlas",
            "--owner",
            "Josh+Echo",
            "--xpub",
            "xpub6CMHQ9GybwBEXAMPLEKEYXPm4o9saiN",
            "--fingerprint",
            "61f21543",
            "--path",
            "m/44h/0h/0h",
            "--export",
            str(export_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    wallets = payload["ledger"]["wallets"]
    assert wallets["61f21543"]["metadata"]["derivation_path"] == "m/44h/0h/0h"
    assert payload["issued_at"] == FIXED_TIME
