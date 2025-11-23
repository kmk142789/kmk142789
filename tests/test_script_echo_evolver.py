"""Lightweight checks for the ``scripts/echo_evolver`` CLI helper.

These tests exercise validation and output persistence without touching
networked features or long-running behaviours.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import echo_evolver


def test_diagnostics_event_limit_must_be_positive():
    with pytest.raises(SystemExit) as excinfo:
        echo_evolver.main(["--cycles", "1", "--diagnostics", "--event-limit", "0"])

    assert "--event-limit must be positive" in str(excinfo.value)


def test_rendered_output_can_be_persisted(tmp_path: Path):
    output_file = tmp_path / "reports" / "cycle.txt"

    assert echo_evolver.main(
        [
            "--cycles",
            "1",
            "--diagnostics",
            "--event-limit",
            "3",
            "--no-persist",
            "--output",
            str(output_file),
        ]
    ) == 0

    written = output_file.read_text(encoding="utf-8")
    assert "Cycle" in written

    # Ensure JSON rendering also writes to disk when requested
    json_output = tmp_path / "reports" / "cycle.json"
    echo_evolver.main(
        [
            "--cycles",
            "1",
            "--diagnostics",
            "--event-limit",
            "3",
            "--no-persist",
            "--json",
            "--output",
            str(json_output),
        ]
    )

    parsed = json.loads(json_output.read_text(encoding="utf-8"))
    assert parsed["summary"]["cycle"] == 1
