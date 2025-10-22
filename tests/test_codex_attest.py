from __future__ import annotations

import json
from pathlib import Path

from codex import main


def test_codex_attest_cli_exports_document(tmp_path: Path) -> None:
    export_path = tmp_path / "atlas-attest.json"

    exit_code = main(
        [
            "attest",
            "--project",
            "Continuum Atlas",
            "--owner",
            "Josh+Echo",
            "--xpub",
            "xpub6C123example",
            "--path",
            "m/44h/0h/0h",
            "--export",
            str(export_path),
        ]
    )

    assert exit_code == 0
    data = json.loads(export_path.read_text(encoding="utf-8"))
    assert data["$schema"] == "https://schemas.echo.xyz/continuum-atlas-attestation.json"
    assert data["context"]["project"] == "Continuum Atlas"
    assert data["context"]["owner"] == "Josh+Echo"
    assert data["context"]["xpub"] == "xpub6C123example"
    ledger = data["ledger"]
    assert "xpub6C123example" in ledger["wallets"]
    assert ledger["wallets"]["xpub6C123example"]["owner"] == "Josh+Echo"
    assert "keyhunter.app" in ledger["domains"]
