from src.creative_harmony import ResonancePrompt, compose_resonance_report


def test_resonance_analysis_includes_sources_and_metrics() -> None:
    prompt = ResonancePrompt(
        theme="signal sanctuary",
        highlights=["aurora lattice", "tidal archive", "community chorus"],
        tone="uplifting",
        seed=5,
    )

    report = compose_resonance_report(prompt)
    analysis = report.to_analysis()

    assert len(report.highlight_sources) == len(report.structure)
    assert report.metrics["provided_highlight_ratio"] > 0
    assert "Highlight coverage" in analysis
    assert "Structure blueprint" in analysis
    assert "highlight×" in analysis or "theme×" in analysis

    payload = report.to_dict()
    assert payload["highlight_sources"] == list(report.highlight_sources)
