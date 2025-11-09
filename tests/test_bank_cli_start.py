import json
from pathlib import Path

from echo.bank.__main__ import main


def test_start_command_bootstraps_scaffolding(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger" / "little_footsteps_bank.jsonl"
    puzzle_path = tmp_path / "puzzles" / "little_footsteps_bank.md"
    proofs_dir = tmp_path / "proofs"
    vault_path = tmp_path / "state" / "vault" / "lf_vault.db"
    treasury_path = tmp_path / "ledger" / "treasury.json"
    link_path = tmp_path / "state" / "links.json"

    exit_code = main(
        [
            "start",
            "--bank",
            "Test Footsteps Bank",
            "--ledger-path",
            str(ledger_path),
            "--puzzle-path",
            str(puzzle_path),
            "--proofs-dir",
            str(proofs_dir),
            "--vault-path",
            str(vault_path),
            "--vault-passphrase",
            "test-passphrase",
            "--treasury-ledger",
            str(treasury_path),
            "--link-path",
            str(link_path),
        ]
    )

    assert exit_code == 0
    assert ledger_path.exists()
    assert proofs_dir.is_dir()

    assert puzzle_path.exists()
    content = puzzle_path.read_text(encoding="utf-8")
    assert "Little Footsteps Bank Sovereign Ledger" in content

    assert vault_path.exists()
    assert treasury_path.exists()
    assert json.loads(treasury_path.read_text(encoding="utf-8")) == []

    assert link_path.exists()
    manifest = json.loads(link_path.read_text(encoding="utf-8"))
    assert manifest["bank"] == "Test Footsteps Bank"
    assert manifest["beneficiary"] == "Little Footsteps"
    assert manifest["ledger"]["path"] == str(ledger_path.resolve())
    assert manifest["ledger"]["puzzle"] == str(puzzle_path.resolve())
    assert manifest["ledger"]["proofs"] == str(proofs_dir.resolve())
    assert manifest["vault"]["path"] == str(vault_path.resolve())
    expected_audit = vault_path.resolve().with_name(f"{vault_path.resolve().stem}_rotation_audit.jsonl")
    assert manifest["vault"]["rotation_audit"] == str(expected_audit)
    assert manifest["treasury"]["ledger_path"] == str(treasury_path.resolve())
