"""Tests for the Resonant Nexus Engine."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from tools.resonant_nexus_engine import (
    EntropyPlugin,
    ResonantNexusEngine,
    TelemetryPlugin,
    load_config,
)


@pytest.mark.asyncio
async def test_engine_generates_report(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    telemetry_path = tmp_path / "telemetry.json"

    engine = ResonantNexusEngine()
    engine.register_plugin(EntropyPlugin(volatility=0.02))
    engine.register_plugin(TelemetryPlugin(sink=telemetry_path))

    await engine.run(2)
    engine.write_report(report_path)

    data = json.loads(report_path.read_text())
    assert data["variance"] >= 0
    assert len(data["cycles"]) == 2
    assert json.loads(telemetry_path.read_text())[-1]["cycle"] == 1


@pytest.mark.asyncio
async def test_engine_respects_custom_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"base_charge": 0.9}))

    config = load_config(str(config_path))
    engine = ResonantNexusEngine(config=config)
    await engine.run(1)

    [state] = engine.history()
    assert state.charge <= 1.0
    assert state.charge >= 0.0
    assert state.ledger[-1] == "cycle:complete"
