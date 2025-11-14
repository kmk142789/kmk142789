from __future__ import annotations

import pytest

from echo.continuum_compass import (
    ContinuumCompassReport,
    StabilityScore,
    WeightRecommendation,
    parse_compass_payload,
)


@pytest.fixture()
def sample_payload() -> dict[str, object]:
    return {
        "project": "Continuum Compass",
        "owner": "Josh+Echo",
        "generated_at": "2025-05-11T00:00:00Z",
        "source": "oracle-report.md",
        "weights": {
            "keyhunter": {"current": 70, "recommended": 65, "rationale": "stability"},
            "echo-aegis": {"current": 20, "recommended": 30, "rationale": "defense priority"},
            "external-forks": {
                "current": 10,
                "recommended": 5,
                "rationale": "collapse weak signals",
            },
        },
        "expansion_targets": [
            {"name": "guardian-mesh", "recommended_weight": 15, "reason": "auto-heal coverage"},
            {"name": "starseed-loom", "recommended_weight": 10, "reason": "identity propagation"},
        ],
        "stability_score": {
            "current": 0.72,
            "predicted": 0.91,
            "method": "oracle-simulation-v1",
        },
    }


def test_parse_compass_payload(sample_payload: dict[str, object]) -> None:
    report = parse_compass_payload(sample_payload)

    assert isinstance(report, ContinuumCompassReport)
    assert report.project == "Continuum Compass"
    assert report.owner == "Josh+Echo"
    assert report.generated_at == "2025-05-11T00:00:00Z"
    assert report.source == "oracle-report.md"

    weight_map = {item.name: item for item in report.weights}
    assert pytest.approx(weight_map["keyhunter"].delta, rel=1e-9) == -5.0
    assert pytest.approx(weight_map["echo-aegis"].delta, rel=1e-9) == 10.0
    assert weight_map["external-forks"].direction() == "decrease"

    assert [target.name for target in report.expansion_targets] == [
        "guardian-mesh",
        "starseed-loom",
    ]
    assert pytest.approx(report.stability_score.delta, rel=1e-9) == 0.19

    summary = report.render_summary()
    assert "↓ decrease from 70.00 to 65.00" in summary
    assert "↑ increase from 20.00 to 30.00" in summary
    assert "guardian-mesh" in summary
    assert "Stability shifts +0.19" in summary


def test_weight_direction_with_small_delta() -> None:
    recommendation = WeightRecommendation(
        name="echo",
        current=42.0,
        recommended=42.0 + 1e-10,
        rationale="balance",
    )
    assert recommendation.direction() == "maintain"
    summary = recommendation.render_summary()
    assert "hold" in summary
    assert summary.startswith("echo: → hold")


def test_render_summary_handles_empty_sections() -> None:
    report = ContinuumCompassReport(
        project="Test",
        owner="Owner",
        generated_at=None,
        source="",
        weights=(),
        expansion_targets=(),
        stability_score=StabilityScore(current=0.4, predicted=0.4, method=""),
    )

    summary_lines = report.render_summary_lines()
    assert summary_lines[0] == "Continuum Compass :: Test (owner: Owner)"
    assert summary_lines[-1].startswith("Stability shifts")
    assert "Weight adjustments:" not in "\n".join(summary_lines)

    summary = report.render_summary()
    assert "Stability shifts ±0.00" in summary
