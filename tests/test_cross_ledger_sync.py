from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

from echo.atlas.temporal_ledger import TemporalLedger
from echo.pulse import CrossLedgerSynchronizer, PulseLedger


def _log_receipt(ledger: PulseLedger, timestamp: datetime, *, diff: str) -> str:
    with patch.object(PulseLedger, "_timestamp", return_value=timestamp):
        receipt = ledger.log(
            diff_signature=diff,
            actor="echo",
            result="ok",
            seed="seed",
        )
    return receipt.signature


def test_cross_ledger_sync_appends_and_deduplicates(tmp_path) -> None:
    pulse_root = tmp_path / "pulse"
    state_dir = tmp_path / "state"
    pulse_ledger = PulseLedger(root=pulse_root)

    first_ts = datetime(2024, 1, 1, 12, 30, tzinfo=timezone.utc)
    second_ts = datetime(2024, 1, 2, 15, 45, tzinfo=timezone.utc)

    first_signature = _log_receipt(pulse_ledger, first_ts, diff="diff-one")
    second_signature = _log_receipt(pulse_ledger, second_ts, diff="diff-two")

    temporal_ledger = TemporalLedger(state_dir=state_dir)
    synchronizer = CrossLedgerSynchronizer(
        pulse_ledger=pulse_ledger,
        temporal_ledger=temporal_ledger,
        actor="sync",
        action="validated",
    )

    appended = synchronizer.sync()

    assert [entry.proof_id for entry in appended] == [first_signature, second_signature]
    assert [entry.ts for entry in appended] == [first_ts, second_ts]

    entries = temporal_ledger.entries()
    assert len(entries) == 2
    assert entries[0].proof_id == first_signature
    assert entries[1].proof_id == second_signature

    assert synchronizer.sync() == []
    assert temporal_ledger.entries() == entries
