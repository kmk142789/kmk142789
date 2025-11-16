import json
from pathlib import Path

from tools.feature_evolver import FeatureEvolver


def test_run_levels_returns_increasing_complexity(tmp_path: Path) -> None:
    evolver = FeatureEvolver(seed=42)
    insights = evolver.run_levels(4)

    assert [insight.payload["complexity_tier"] for insight in insights] == [1, 2, 3, 4]
    assert insights[0].payload["ideas"][0] == "Telemetry Overlay"
    assert insights[2].payload["order"][0] == "Telemetry Overlay"

    export_path = tmp_path / "insights.json"
    export_path.write_text(json.dumps([insight.payload for insight in insights]))
    exported = json.loads(export_path.read_text())
    assert exported[-1]["complexity_tier"] == 4


def test_simulation_probability_is_deterministic() -> None:
    evolver = FeatureEvolver(seed=7)
    risk = evolver.level_four_risk_simulation(trials=20)
    assert 0.0 <= risk.payload["probability"] <= 1.0
    assert risk.payload["p95_completion"] >= 0
