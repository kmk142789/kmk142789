"""Unit tests for the progressive feature helpers."""
from __future__ import annotations

from datetime import datetime, timezone

from echo_cli.progressive_features import (
    analyze_text_corpus,
    evaluate_strategy_matrix,
    forecast_operational_resilience,
    generate_numeric_intelligence,
    simulate_delivery_timeline,
)


def test_generate_numeric_intelligence_sequence_and_ratio() -> None:
    report = generate_numeric_intelligence(6)
    assert report["sequence"] == [1, 1, 2, 3, 5, 8]
    assert report["stats"]["even"] == 2
    assert report["stats"]["odd"] == 4
    assert report["golden_ratio_estimate"] == report["ratio_trend"][-1]
    assert report["ratio_trend"][-1] == 8 / 5


def test_analyze_text_corpus_identifies_top_tokens() -> None:
    corpus = [
        "Echo writes radiant code for the world.",
        "The world replies: echo, echo, echo!",
    ]
    summary = analyze_text_corpus(corpus)
    assert summary["documents"] == 2
    assert summary["total_words"] == 13
    assert summary["top_tokens"][0]["token"] == "echo"
    assert summary["top_tokens"][0]["count"] == 4


def test_simulate_delivery_timeline_adds_buffers() -> None:
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    result = simulate_delivery_timeline(
        [
            {"name": "Design", "duration": 3, "confidence": 0.9},
            {"name": "Build", "duration": 5, "confidence": 0.7},
        ],
        start=start,
    )
    assert result["start"] == "2024-01-01T00:00:00Z"
    assert result["timeline"][0]["buffer_days"] >= 0.25
    assert result["timeline"][1]["start"] == result["timeline"][0]["buffer_end"]
    assert result["risk"]["classification"] in {"low", "medium", "high"}


def test_evaluate_strategy_matrix_ranks_options() -> None:
    report = evaluate_strategy_matrix(
        [
            {"name": "Nova", "impact": 9, "effort": 4, "confidence": 0.8},
            {"name": "Pulse", "impact": 7, "effort": 3, "confidence": 0.9},
        ],
        {"impact": 0.6, "effort": 0.2, "confidence": 0.2},
    )
    assert report["best_option"]["name"] == "Nova"
    assert report["options"][0]["score"] > report["options"][1]["score"]
    assert report["criteria"]["impact"] == 0.6
    assert report["options"][0]["relative_score"] == 1.0


def test_forecast_operational_resilience_computes_expected_hours() -> None:
    start = datetime(2024, 5, 1, tzinfo=timezone.utc)
    forecast = forecast_operational_resilience(
        [
            {"name": "Data center outage", "likelihood": 0.4, "impact_hours": 12, "recovery_hours": 6},
            {"name": "Network spike", "likelihood": 0.2, "impact_hours": 6, "recovery_hours": 4},
        ],
        start=start,
        horizon_hours=120,
    )
    assert forecast["start"] == "2024-05-01T00:00:00Z"
    assert forecast["expected_disruption_hours"] > 0
    assert len(forecast["timeline"]) == 2
    assert forecast["timeline"][0]["window_start"] == "2024-05-01T00:00:00Z"
    assert forecast["risk"]["classification"] in {"stable", "watch", "critical"}
