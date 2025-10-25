from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from echo.transcend import TranscendOrchestrator


class DummyLoop:
    def __init__(self, cycle: int, state_path: Path) -> None:
        self.cycle = cycle
        self.state_path = state_path
        self.calls: list[str] = []

    def progress(self, summary: str, *, actor: str = "transcend") -> object:
        self.calls.append(summary)
        return SimpleNamespace(
            cycle=self.cycle,
            proposal_id=f"loop/cycle-{self.cycle:04d}",
            next_proposal_id=f"loop/cycle-{self.cycle + 1:04d}",
            state_path=self.state_path,
        )


class NullLoop:
    def progress(self, summary: str, *, actor: str = "transcend") -> None:  # pragma: no cover - stub
        return None


def test_transcend_orchestrator_records_cycle(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    log_path = docs_dir / "COLOSSUS_LOG.md"
    log_path.write_text("# COLOSSUS Expansion Log\n", encoding="utf-8")

    cycle = 4
    timestamp = "2025-05-11T00:00:00Z"
    glyph = "∇⊸≋∇::abcd"
    artifacts = [
        "colossus/cycle_00004/puzzle_cycle_00004.md",
        "colossus/cycle_00004/dataset_cycle_00004.json",
        "colossus/cycle_00004/glyph_narrative_00004.md",
    ]

    def fake_cycle() -> None:
        payload = (
            f"- {timestamp} | Cycle {cycle:05d} | Glyph {glyph} | "
            f"Artifacts: {', '.join(artifacts)}\n"
        )
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(payload)

    ledger_path = tmp_path / "ledger" / "transcend_log.jsonl"
    ritual_dir = tmp_path / "ledger" / "rituals"
    stream_dir = tmp_path / "ledger" / "streams"
    loop_state = tmp_path / "state" / "self_sustaining_loop.json"
    dummy_loop = DummyLoop(cycle, loop_state)

    orchestrator = TranscendOrchestrator(
        base_dir=tmp_path,
        interval_minutes=0.0,
        max_cycles=1,
        targets=("github", "firebase"),
        ledger_path=ledger_path,
        ritual_dir=ritual_dir,
        stream_dir=stream_dir,
        cycle_executor=fake_cycle,
        planning_loop=dummy_loop,
    )

    records = list(orchestrator.run())
    assert len(records) == 1
    record = records[0]

    assert record.cycle == cycle
    assert record.timestamp == timestamp
    assert record.glyph_signature == glyph
    assert list(record.artifacts) == artifacts
    assert record.ritual_path.exists()
    assert "Glyph Signature" in record.ritual_path.read_text(encoding="utf-8")

    ledger_entries = [
        json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line
    ]
    assert ledger_entries[0]["cycle"] == cycle
    assert ledger_entries[0]["targets"] == ["github", "firebase"]
    assert ledger_entries[0]["artifacts"] == artifacts
    assert ledger_entries[0]["progress"]["proposal_id"] == "loop/cycle-0004"

    for target in ("github", "firebase"):
        sync_path = stream_dir / f"{target}.log"
        assert sync_path.exists()
        assert f"cycle={cycle:05d}" in sync_path.read_text(encoding="utf-8")

    assert dummy_loop.calls
    assert glyph in dummy_loop.calls[0]


@pytest.mark.parametrize(
    "interval_minutes, at_midnight, recorded_at, now, expected",
    [
        (
            30.0,
            False,
            datetime(2025, 5, 11, 10, 0, tzinfo=timezone.utc),
            datetime(2025, 5, 11, 10, 10, tzinfo=timezone.utc),
            20 * 60,
        ),
        (
            0.0,
            True,
            datetime(2025, 5, 11, 6, 30, tzinfo=timezone.utc),
            datetime(2025, 5, 11, 12, 0, tzinfo=timezone.utc),
            (datetime(2025, 5, 12, tzinfo=timezone.utc) - datetime(2025, 5, 11, 12, 0, tzinfo=timezone.utc)).total_seconds(),
        ),
    ],
)
def test_transcend_schedule_calculations(
    tmp_path: Path,
    interval_minutes: float,
    at_midnight: bool,
    recorded_at: datetime,
    now: datetime,
    expected: float,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "COLOSSUS_LOG.md").write_text("", encoding="utf-8")

    orchestrator = TranscendOrchestrator(
        base_dir=tmp_path,
        interval_minutes=interval_minutes,
        at_midnight=at_midnight,
        max_cycles=1,
        targets=("github",),
        ledger_path=tmp_path / "ledger" / "transcend_log.jsonl",
        ritual_dir=tmp_path / "ledger" / "rituals",
        stream_dir=tmp_path / "ledger" / "streams",
        cycle_executor=lambda: None,
        planning_loop=NullLoop(),
    )

    result = orchestrator._seconds_until_next_cycle(recorded_at=recorded_at, now=now)
    assert pytest.approx(result) == expected
