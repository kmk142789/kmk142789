from src.creative_harmony import ResonancePrompt, compose_resonance_report


def test_resonance_report_summary_and_metrics() -> None:
    prompt = ResonancePrompt(
        theme="luminous archive",
        highlights=["signal threads", "signal threads", "aurora passages"],
        tone="warm",
        seed=11,
    )

    report = compose_resonance_report(prompt)

    metrics = report.metrics
    assert metrics["transition_count"] == len(report.transitions)
    assert metrics["unique_highlights"] <= len(report.highlights_used)
    assert metrics["sentence_count"] == len(report.structure) + len(report.transitions)

    summary = report.to_summary()
    assert "Resonance snapshot" in summary
    assert f"unique_highlights={metrics['unique_highlights']}" in summary
    assert prompt.theme in summary
