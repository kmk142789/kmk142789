from __future__ import annotations

from datetime import datetime, timezone

from echo.atlas.temporal_ledger import LedgerEntryInput, TemporalLedger, render_markdown, render_svg


def test_append_and_render(tmp_path):
    ledger = TemporalLedger(state_dir=tmp_path)
    base = datetime(2025, 1, 1, tzinfo=timezone.utc)
    entries = []
    for index in range(3):
        harmonix = None
        if index == 1:
            harmonix = {
                "snapshot_id": "harmonix::cycle-0001",
                "cycle": 1,
                "timestamp": base,
                "recursion_hash": "deadbeefcafefeed",
            }
        entry = ledger.append(
            LedgerEntryInput(
                actor="actor",
                action=f"action-{index}",
                ref=f"ref-{index}",
                proof_id=f"proof-{index}",
                ts=base,
                harmonix=harmonix,
            )
        )
        entries.append(entry)

    stored = list(ledger.iter_entries())
    assert len(stored) == 3
    assert stored[0].hash == entries[0].hash
    assert stored[1].harmonix is not None
    assert stored[1].harmonix.recursion_hash == "deadbeefcafefeed"

    markdown = render_markdown(stored)
    assert "Temporal Ledger Snapshot" in markdown
    assert "proof-0" in markdown
    assert "harmonix::cycle-0001" in markdown

    svg = render_svg(stored)
    assert svg.startswith("<svg")
    assert "action-1" in svg
    assert "harmonix: harmonix::cycle-0001" in svg

    dot = ledger.as_dot()
    assert "digraph TemporalLedger" in dot
    assert "Harmonix harmonix::cycle-0001" in dot
