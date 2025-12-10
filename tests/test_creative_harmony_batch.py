from dataclasses import replace

from src.creative_harmony import (
    ResonancePrompt,
    compose_resonance_batch,
    compose_resonance_report,
)


def test_compose_resonance_batch_uses_incrementing_seeds() -> None:
    prompt = ResonancePrompt(
        theme="aurora",
        highlights=["signal", "echo"],
        tone="warm",
        seed=10,
    )

    reports = compose_resonance_batch(prompt, runs=3)

    assert len(reports) == 3
    seeds = [report.seed for report in reports]
    assert seeds == [10, 11, 12]


def test_batch_with_override_matches_single_report() -> None:
    prompt = ResonancePrompt(theme="archive", highlights=["signal"], tone="calm")

    batch_report = compose_resonance_batch(prompt, runs=1, seed_start=5)[0]
    single_report = compose_resonance_report(replace(prompt, seed=5))

    assert batch_report.text == single_report.text
    assert batch_report.metrics == single_report.metrics
