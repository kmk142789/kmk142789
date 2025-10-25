from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from echo.pulse.analytics import (
    PulseSummary,
    render_summary_table,
    summarize_ledger,
    summarize_receipts,
)
from echo.pulse.ledger import PulseLedger, PulseReceipt


def _make_receipt(
    *,
    path: Path,
    actor: str,
    result: str,
    seed: str,
    time: str,
) -> PulseReceipt:
    return PulseReceipt(
        sha256_of_diff="hash",
        time=time,
        actor=actor,
        rhyme="rhyme",
        result=result,
        seed=seed,
        signature="signature",
        path=path,
    )


def test_summarize_receipts_counts_and_latest(tmp_path: Path) -> None:
    receipts = [
        _make_receipt(
            path=tmp_path / "one.json",
            actor="alpha",
            result="success",
            seed="seed-1",
            time="2024-05-01T12:00:00+00:00",
        ),
        _make_receipt(
            path=tmp_path / "two.json",
            actor="alpha",
            result="failure",
            seed="seed-2",
            time="2024-05-02T12:00:00+00:00",
        ),
        _make_receipt(
            path=tmp_path / "three.json",
            actor="beta",
            result="success",
            seed="seed-3",
            time="2024-05-03T12:00:00+00:00",
        ),
    ]

    summary = summarize_receipts(receipts)

    assert isinstance(summary, PulseSummary)
    assert summary.total_receipts == 3
    assert summary.unique_actors == ("alpha", "beta")
    assert summary.actor_counts["alpha"] == 2
    assert summary.result_counts["success"] == 2
    assert summary.latest_time == datetime(2024, 5, 3, 12, 0, tzinfo=timezone.utc)
    assert summary.seeds == ("seed-1", "seed-2", "seed-3")


def test_render_summary_table_handles_empty() -> None:
    empty_summary = PulseSummary(
        total_receipts=0,
        unique_actors=(),
        actor_counts={},
        result_counts={},
        seeds=(),
        latest_time=None,
    )

    message = render_summary_table(empty_summary)
    assert "No pulse receipts" in message


def test_summarize_ledger_respects_limit(tmp_path: Path) -> None:
    ledger = PulseLedger(root=tmp_path)
    timestamps = [
        datetime(2024, 5, 1, 10, 0, tzinfo=timezone.utc),
        datetime(2024, 5, 2, 11, 30, tzinfo=timezone.utc),
        datetime(2024, 5, 3, 9, 15, tzinfo=timezone.utc),
    ]

    for index, timestamp in enumerate(timestamps):
        with patch.object(PulseLedger, "_timestamp", return_value=timestamp):
            ledger.log(
                diff_signature=f"diff-{index}",
                actor="alpha" if index < 2 else "beta",
                result="success" if index != 1 else "failure",
                seed=f"seed-{index}",
            )

    summary = summarize_ledger(ledger, limit=2)

    assert summary.total_receipts == 2
    assert summary.latest_time == timestamps[-1]
    assert summary.unique_actors[0] in {"alpha", "beta"}
    assert {"seed-2", "seed-1"}.issuperset(summary.seeds)
