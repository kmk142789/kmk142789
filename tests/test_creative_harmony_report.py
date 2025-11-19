from src.creative_harmony import (
    ResonancePrompt,
    compose_resonance,
    compose_resonance_report,
)


def test_compose_resonance_report_matches_text_output() -> None:
    prompt = ResonancePrompt(
        theme="signal sanctuary",
        highlights=["aurora lattice", "tidal archive"],
        tone="uplifting",
        seed=7,
    )

    report = compose_resonance_report(prompt)

    assert report.text == compose_resonance(prompt)
    assert report.structure  # blueprint persisted
    assert len(report.highlights_used) == len(report.structure)



def test_resonance_report_serialisation() -> None:
    prompt = ResonancePrompt(
        theme="harmonic bloom",
        highlights=["community beacon"],
        tone="warm",
        seed=3,
    )

    report = compose_resonance_report(prompt)
    payload = report.to_dict()

    assert payload["text"].startswith("Resonance for 'harmonic bloom'")
    assert payload["structure"] == list(report.structure)
    assert payload["transitions"] == list(report.transitions)
    assert payload["highlights_used"] == list(report.highlights_used)
    assert payload["timestamp"] == report.timestamp
