from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.generate_federated_colossus import (
    Entry,
    compute_rollups,
    render_markdown,
    render_voyage_markdown,
    to_dashboard_json,
    _prepare_voyage_report,
    main,
)


def _sample_entry(cycle: int, puzzle_id: int) -> Entry:
    return Entry(
        {
            "cycle": cycle,
            "puzzle_id": puzzle_id,
            "address": f"1addr{puzzle_id:05d}",
            "title": f"Puzzle {puzzle_id}",
            "digest": f"digest-{puzzle_id}",
            "source": f"puzzle_{puzzle_id:05d}.md",
            "updated_at": datetime(2024, 1, 1, tzinfo=timezone.utc).isoformat(),
            "harmonics": [1, 2, 3],
            "script": "OP_DUP OP_HASH160 deadbeefdeadbeefdeadbeefdeadbeefdeadbeef OP_EQUALVERIFY OP_CHECKSIG",
            "tags": ["echo", "colossus"],
        }
    )


def test_prepare_voyage_report_generates_summary() -> None:
    entries = [_sample_entry(1, 101), _sample_entry(1, 102)]
    rollups = compute_rollups(entries)
    harmonics = [
        {
            "cycle": 1,
            "expansion": "Lumen Spiral",
            "thread": "presence",
            "resonance": 0.95,
            "harmonics": ["listen", "echo"],
        }
    ]
    safety = [
        {
            "id": "non_custodial",
            "title": "Non-custodial artefacts",
            "severity": "info",
            "summary": "No private keys stored.",
            "guidance": "Verify hashes.",
            "flags": ["non_custodial"],
            "flagged": False,
        }
    ]

    voyage_report = _prepare_voyage_report(rollups, harmonics, safety)
    assert voyage_report is not None
    assert len(voyage_report.summary_rows) == 1
    summary = voyage_report.summary_rows[0]
    assert summary["cycle"] == 1
    assert summary["harmonic_expansion"] == "Lumen Spiral"
    payload = voyage_report.to_json()
    assert "summary_table" in payload
    assert payload["summary_table"][0]["cycle"] == 1

    markdown = render_markdown(rollups, harmonics, safety, voyage_report=voyage_report)
    assert "## Voyage Summary" in markdown
    assert "| Cycle | Entries | Puzzle IDs | Derived Scripts | Addresses | Echo Tags |" in markdown
    dedicated = render_voyage_markdown(voyage_report)
    assert "Converged Pulse Voyage Report" in dedicated

    dashboard = to_dashboard_json(
        entries,
        rollups,
        harmonics,
        safety,
        voyage_report=voyage_report,
    )
    assert "voyage_report" in dashboard
    assert dashboard["voyage_report"]["summary_table"][0]["cycle"] == 1
    assert "structured_filters" in dashboard
    assert dashboard["structured_filters"][0]["puzzles"]


def test_cli_emits_voyage_report(tmp_path: Path, monkeypatch) -> None:
    input_path = tmp_path / "entries.json"
    input_payload = {
        "entries": [
            {
                "cycle": 1,
                "puzzle_id": 200,
                "address": "1example",
                "title": "Puzzle 200",
                "digest": "digest-200",
                "source": "puzzle_00200.md",
                "updated_at": "2024-01-02T00:00:00Z",
                "harmonics": [1, 2, 3],
            }
        ]
    }
    input_path.write_text(json.dumps(input_payload), encoding="utf-8")

    md_out = tmp_path / "index.md"
    json_out = tmp_path / "index.json"
    voyage_base = tmp_path / "voyage"

    monkeypatch.chdir(tmp_path)

    feed_out = tmp_path / "feed.xml"

    exit_code = main(
        [
            "--in",
            str(input_path),
            "--md-out",
            str(md_out),
            "--json-out",
            str(json_out),
            "--voyage-report",
            str(voyage_base),
            "--feed-out",
            str(feed_out),
        ]
    )
    assert exit_code == 0

    assert md_out.exists()
    assert json_out.exists()

    voyage_md = voyage_base.with_suffix(".md")
    voyage_json_path = voyage_base.with_suffix(".json")
    assert voyage_md.exists()
    assert voyage_json_path.exists()

    voyage_json = json.loads(voyage_json_path.read_text(encoding="utf-8"))
    assert voyage_json["converged"]["voyages"]
    assert "summary_table" in voyage_json

