"""Tests for voice biasing and export utilities in :mod:`src.creative_loop`."""

from __future__ import annotations

import json
from pathlib import Path

from src.creative_loop import (
    LoopSeed,
    compose_loop,
    export_loop_result,
    generate_loop,
)


def test_voice_bias_prioritises_requested_voice() -> None:
    """Voice bias weights should steer the first selected voice deterministically."""

    seed = LoopSeed(
        motif="signal bloom",
        fragments=("pulse", "beam"),
        tempo="allegro",
        pulses=3,
        seed=11,
        voice_bias={"signal": 5.0},
    )

    loop_result = generate_loop(seed)
    assert loop_result.timeline[0]["voice"] == "signal"
    assert loop_result.summary is not None
    rendered = compose_loop(seed, format="text", loop_result=loop_result)
    assert "[summary]" in rendered


def test_export_loop_result_json(tmp_path: Path) -> None:
    """Export helper should write JSON payloads that include the summary."""

    seed = LoopSeed(motif="echo", fragments=(), pulses=2, seed=5)
    loop_result = generate_loop(seed)
    export_path = tmp_path / "loop.json"
    exported = export_loop_result(export_path, loop_result, seed, format="json")

    assert exported.exists()
    data = json.loads(exported.read_text())
    assert data["loop"]["summary"]
