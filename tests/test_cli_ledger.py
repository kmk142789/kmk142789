from __future__ import annotations

from datetime import datetime, timezone

from echo.atlas.temporal_ledger import LedgerEntryInput, TemporalLedger
from echo.cli import main


def test_cli_snapshot_and_tail(tmp_path, capsys):
    state = tmp_path / "state"
    state.mkdir()
    ledger = TemporalLedger(state_dir=state)
    ledger.append(
        LedgerEntryInput(
            actor="cli",
            action="emit",
            ref="ref-1",
            proof_id="proof-1",
            ts=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
    )

    out_dir = tmp_path / "artifacts"
    code = main(
        [
            "ledger",
            "snapshot",
            "--format",
            "md",
            "--out",
            str(out_dir),
            "--state",
            str(state),
        ]
    )
    assert code == 0
    snapshot = out_dir / "ledger_snapshot.md"
    assert snapshot.exists()

    code = main(["ledger", "tail", "--state", str(state), "--limit", "5"])
    assert code == 0
    captured = capsys.readouterr()
    assert "cli" in captured.out
