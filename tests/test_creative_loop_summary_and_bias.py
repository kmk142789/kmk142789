"""Tests for summary output, suite export, and voice bias profiles."""

from __future__ import annotations

import json
from pathlib import Path

from src.creative_loop import (
    LoopSeed,
    compose_loop,
    export_suite_summary,
    generate_loop,
    load_voice_bias_profile,
    summarise_loop_suite,
)


def test_summary_format_emphasises_metrics() -> None:
    """Summary format should highlight high-level metrics for a loop."""

    seed = LoopSeed(motif="lattice", fragments=("signal",), pulses=2, seed=3)
    text = compose_loop(seed, format="summary")
    lines = text.splitlines()

    assert lines[0].startswith("Loop for 'lattice'")
    assert any(line.startswith("Voice diversity:") for line in lines)
    assert any(line.startswith("Diagnostics:") for line in lines)


def test_export_suite_summary_persists_json(tmp_path: Path) -> None:
    """Aggregated suite summaries should be serialisable as JSON."""

    seed = LoopSeed(motif="pulse", fragments=("beam",), pulses=1, seed=7)
    result = generate_loop(seed)
    summary = summarise_loop_suite([result])
    target = tmp_path / "suite.json"

    exported = export_suite_summary(summary, target)

    assert exported.exists()
    payload = json.loads(exported.read_text())
    assert payload["total_loops"] == 1
    assert payload["total_lines"] >= 1


def test_load_voice_bias_profile_filters_invalid(tmp_path: Path) -> None:
    """Voice bias profile loader should ignore invalid voices and weights."""

    profile_path = tmp_path / "bias.json"
    profile_path.write_text(
        json.dumps(
            {
                "signal": 4,
                "unknown": 10,
                "dream": "2.5",
                "chorus": 0,
            }
        ),
        encoding="utf-8",
    )

    profile = load_voice_bias_profile(profile_path)

    assert profile == {"signal": 4.0, "dream": 2.5}
