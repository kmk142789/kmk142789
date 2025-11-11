from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from echo.ecosystem_pulse import EcosystemPulseReport, EcosystemSignal
from echo.strategic_vector import (
    StrategicSignal,
    StrategicVectorReport,
    build_strategic_vector,
    export_strategic_vector,
)


def _dt(days_ago: int) -> str:
    moment = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return moment.isoformat()


def test_strategic_vector_handles_empty_inputs(tmp_path: Path) -> None:
    report = build_strategic_vector(
        manifest_entries=[], timeline_cycles=[], ecosystem_report=None, capability_registry={}
    )
    assert isinstance(report, StrategicVectorReport)
    assert report.overall_score == 0.0
    assert all(signal.score == 0.0 for signal in report.signals)

    # round-trip export sanity check for empty reports
    json_path = export_strategic_vector(report, tmp_path / "vector.json")
    markdown_path = export_strategic_vector(report, tmp_path / "vector.md", format="markdown")
    assert json_path.exists()
    assert markdown_path.exists()


def test_strategic_vector_combines_multiple_signals() -> None:
    manifest_entries = [
        {
            "name": "Core Engine",
            "category": "runtime",
            "tags": ["core", "python"],
            "owners": ["@echo/core"],
            "last_modified": _dt(3),
        },
        {
            "name": "Governance Capsule",
            "category": "governance",
            "tags": ["charter", "policy"],
            "owners": ["@echo/gov"],
            "last_modified": _dt(15),
        },
        {
            "name": "Pulse Dashboard",
            "category": "ops",
            "tags": ["dashboard", "pulse"],
            "owners": ["@echo/ops"],
            "last_modified": _dt(45),
        },
    ]

    now = datetime.now(timezone.utc)
    timeline_cycles = [
        {
            "snapshot": {
                "cycle": 1,
                "index": 88.2,
                "timestamp": (now - timedelta(days=5)).isoformat(),
                "metrics": {"cohesion": 95.0},
            },
            "pulses": [{"message": "alpha"}, {"message": "beta"}],
            "puzzles": [{"id": 1}],
            "harmonics": [{"name": "thread"}],
        },
        {
            "snapshot": {
                "cycle": 2,
                "index": 90.5,
                "timestamp": (now - timedelta(days=9)).isoformat(),
                "metrics": {"cohesion": 97.0},
            },
            "pulses": [{"message": "gamma"}],
            "puzzles": [],
            "harmonics": [],
        },
    ]

    ecosystem_report = EcosystemPulseReport(
        generated_at=now,
        signals=[
            EcosystemSignal(
                key="core",
                title="Core Runtime",
                description="",
                path=Path("packages/core"),
                file_count=120,
                last_updated=now,
                score=88.0,
            ),
            EcosystemSignal(
                key="ops",
                title="Operations",
                description="",
                path=Path("ops"),
                file_count=14,
                last_updated=now - timedelta(days=30),
                score=62.0,
                insights=["Refresh incident simulations."],
            ),
        ],
    )

    capability_registry = {
        "strategic_planner": {
            "description": "Generates sovereign strategic plans for Echo evolution.",
        },
        "pulse_analysis": {
            "description": "Analyses pulse cadence / resonance patterns for operators.",
        },
        "ledger_guardian": {
            "description": "Maintains proof ledgers ensuring cryptographic fidelity.",
        },
    }

    report = build_strategic_vector(
        manifest_entries=manifest_entries,
        timeline_cycles=timeline_cycles,
        ecosystem_report=ecosystem_report,
        capability_registry=capability_registry,
        generated_at=now,
    )

    assert report.overall_score > 0.0
    assert report.overall_score <= 1.0

    signal_map = {signal.name: signal for signal in report.signals}
    assert set(signal_map) == {"manifest", "timeline", "capabilities", "ecosystem"}
    assert signal_map["manifest"].score > 0.4
    assert signal_map["timeline"].score > 0.2
    assert signal_map["capabilities"].score > 0.1
    assert signal_map["ecosystem"].score > 0.4

    # ensure metadata mirrors inputs
    assert report.metadata["manifest_entries"] == len(manifest_entries)
    assert report.metadata["timeline_cycles"] == len(timeline_cycles)
    assert report.metadata["capability_count"] == len(capability_registry)
    assert report.metadata["ecosystem_surface"] == len(ecosystem_report.signals)


def test_strategic_vector_signal_serialisation() -> None:
    signal = StrategicSignal(
        name="demo",
        title="Demo",
        score=0.75,
        weight=0.5,
        summary="demo summary",
        details={"key": "value"},
        insights=("insight",),
    )
    report = StrategicVectorReport(
        generated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        signals=(signal,),
        metadata={"example": 1},
    )

    payload = report.to_dict()
    assert payload["overall_score"] == 0.75
    assert payload["signals"][0]["name"] == "demo"
    markdown = report.render_markdown()
    assert "Demo" in markdown
    assert "Composite score" in markdown
