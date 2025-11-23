from src.creative_harmony import ResonancePrompt, compose_resonance_report


def test_report_includes_prompt_metadata_and_trace():
    prompt = ResonancePrompt(
        theme="aurora",
        highlights=["signal", "signal", "echo"],
        tone="warm",
        seed=7,
    )

    report = compose_resonance_report(prompt)
    payload = report.to_dict()

    assert payload["tone"] == "warm"
    assert payload["seed"] == 7
    assert payload["prompt_highlights"] == ["signal", "signal", "echo"]
    assert "signal" in payload["highlight_weights"]

    trace = report.to_trace()
    assert "tone=warm" in trace
    assert "seed=7" in trace
    assert "signal" in trace
