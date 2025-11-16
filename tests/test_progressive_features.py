"""Unit tests for the progressive feature helpers."""
from __future__ import annotations

from datetime import datetime, timezone

from echo_cli.progressive_features import (
    assess_alignment_signals,
    analyze_text_corpus,
    evaluate_operational_readiness,
    forecast_portfolio_throughput,
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


def test_assess_alignment_signals_orders_contributions() -> None:
    payload = assess_alignment_signals(
        {"Focus": 0.82, "Clarity": 0.7, "Cadence": 0.9}, target=0.75
    )
    assert payload["classification"] == "aligned"
    assert payload["focus"]["weakest"] == "Clarity"
    assert payload["signals"][0]["score"] >= payload["signals"][-1]["score"]


def test_operational_readiness_identifies_recommendations() -> None:
    payload = evaluate_operational_readiness(
        [
            {"name": "Core", "coverage": 0.9, "automation": 0.8, "runbooks": 3, "incidents": 0},
            {
                "name": "Edge",
                "coverage": 0.4,
                "automation": 0.3,
                "runbooks": 0,
                "incidents": 6,
            },
        ],
        horizon_weeks=12,
    )
    assert payload["classification"] in {"stable", "elevated", "at-risk"}
    assert len(payload["capabilities"]) == 2
    assert any(entry["status"] != "ready" for entry in payload["capabilities"])
    assert payload["recommendations"]


def test_forecast_portfolio_throughput_respects_dependencies() -> None:
    payload = forecast_portfolio_throughput(
        [
            {"name": "API", "impact": 8, "effort": 5, "confidence": 0.9},
            {
                "name": "UI",
                "impact": 6,
                "effort": 4,
                "confidence": 0.85,
                "dependencies": ["API"],
            },
        ],
        velocity=5,
        horizon_weeks=4,
    )
    assert payload["priority_order"][0]["name"] == "API"
    assert payload["sprint_plan"]
