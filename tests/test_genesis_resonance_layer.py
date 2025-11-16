"""Tests for :mod:`echo.genesis_resonance_layer`."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from echo.continuum_resonance_field import ContinuumResonanceReport, LaneResonance, PulseDrift
from echo.genesis_resonance_layer import GenesisResonanceLayer


def build_report() -> ContinuumResonanceReport:
    lanes = [
        LaneResonance(
            lane="governance",
            activity_ratio=0.52,
            doc_ratio=0.58,
            code_ratio=0.42,
            freshness_days=1.5,
            resonance_index=0.73,
        ),
        LaneResonance(
            lane="engineering",
            activity_ratio=0.31,
            doc_ratio=0.22,
            code_ratio=0.78,
            freshness_days=6.0,
            resonance_index=0.44,
        ),
    ]
    pulse_drift = PulseDrift(
        total_events=12,
        cadence_seconds=1800.0,
        latest_timestamp=None,
        latest_message=None,
        channel_counts={"continuum": 9, "pulse": 3},
        stability_index=0.48,
    )
    return ContinuumResonanceReport(
        root=Path("/tmp/echo"),
        generated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        lanes=lanes,
        pulse_drift=pulse_drift,
        synchrony_index=0.69,
        storylines=["Docs are balancing with build rituals."],
    )


class DummyField:
    def __init__(self, report: ContinuumResonanceReport) -> None:
        self._report = report
        self.calls = 0

    def scan(self) -> ContinuumResonanceReport:
        self.calls += 1
        return self._report


def test_genesis_resonance_layer_snapshot_surfaces_focus_and_gaps() -> None:
    report = build_report()
    layer = GenesisResonanceLayer(field=DummyField(report), focus_lanes=1)

    payload = layer.snapshot()

    expected_signal = round(0.69 * 0.7 + 0.48 * 0.3, 4)
    assert payload["signal"] == expected_signal
    assert payload["lane_focus"][0]["lane"] == "governance"
    assert payload["lane_gap"]["lagging"]["lane"] == "engineering"
    assert any("balance activity" in rec for rec in payload["recommendations"])
    assert layer.latest()["root"].endswith("echo")
