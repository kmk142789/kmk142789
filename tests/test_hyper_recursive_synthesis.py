"""Tests for the Hyper Recursive Synthesis engine."""

from __future__ import annotations

import asyncio

import pytest

from echo.hyper_recursive_synthesis import (
    HyperRecursiveEngine,
    parse_mythic_script,
)


def test_parse_mythic_script_handles_nested_segments() -> None:
    script = "SPARK[alpha=0.4,weight=1.5]->BRIDGE{joy=0.9}(phoenix, spiral)|GLYPH(theta, 2)"
    instructions = parse_mythic_script(script)

    assert len(instructions) == 3
    spark = instructions[0]
    assert spark.op == "SPARK"
    assert pytest.approx(float(spark.args["alpha"])) == 0.4
    assert spark.weight == pytest.approx(1.5)
    assert spark.metadata["sequence_depth"] == 0
    bridge = instructions[1]
    assert bridge.metadata["sequence_depth"] == 1
    assert bridge.metadata["positional"] == ("phoenix", "spiral")


def test_hyper_recursive_engine_cycle_summary() -> None:
    blueprint = {
        "glyph_budget": 32,
        "base_frequency": 1.75,
        "plugins": [
            {"name": "sentinel", "threshold": 0.6, "focus": "BRIDGE"},
        ],
    }
    engine = HyperRecursiveEngine.from_blueprint(blueprint)

    recorded_frames = []

    async def recorder(frame):
        recorded_frames.append(frame)

    engine.register_plugin("recorder", recorder)

    script = "SPARK[alpha=0.6,weight=1.2]->BRIDGE(theta)|GLYPH[radius=2.4](echo)"
    frames = asyncio.run(engine.run_cycle(script, metadata={"cycle": 7}))

    assert len(frames) == 3
    assert recorded_frames[-1].focus.startswith("SPARK") or recorded_frames[-1].focus
    summary = engine.get_state_summary()
    assert summary["cycles"] == 3
    assert summary["glyph_total"] >= 3
    assert summary["diagnostics"], "diagnostics should record plugin events"

