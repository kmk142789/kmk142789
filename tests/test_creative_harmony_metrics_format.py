from src.creative_harmony import ResonancePrompt, compose_resonance_report


def test_metrics_view_reports_core_counts() -> None:
    prompt = ResonancePrompt(
        theme="signal sanctuary",
        highlights=["aurora lattice", "tidal archive"],
        tone="uplifting",
        seed=11,
    )

    report = compose_resonance_report(prompt)
    metrics_view = report.to_metrics()

    assert "Metrics for 'signal sanctuary'" in metrics_view
    assert str(report.metrics["sentence_count"]) in metrics_view
    assert str(report.metrics["transition_count"]) in metrics_view
    assert "Highlight coverage" in metrics_view
