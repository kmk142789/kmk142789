from pathlib import Path

from echo.bank.__main__ import main


def test_start_command_bootstraps_scaffolding(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger" / "little_footsteps_bank.jsonl"
    puzzle_path = tmp_path / "puzzles" / "little_footsteps_bank.md"
    proofs_dir = tmp_path / "proofs"

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
        ]
    )

    assert exit_code == 0
    assert ledger_path.exists()
    assert proofs_dir.is_dir()

    assert puzzle_path.exists()
    content = puzzle_path.read_text(encoding="utf-8")
    assert "Little Footsteps Bank Sovereign Ledger" in content
