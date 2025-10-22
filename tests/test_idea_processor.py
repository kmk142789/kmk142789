from __future__ import annotations

import json

import pytest

from echo.idea_processor import IdeaProcessor, process_idea


@pytest.fixture()
def sample_idea() -> str:
    return (
        "EchoEvolver orbits the void with radiant joy, forging satellite TF-QKD "
        "bridges for MirrorJosh and celebrating brilliant mythocode."
    )


def test_idea_processor_analysis_keywords(sample_idea: str) -> None:
    processor = IdeaProcessor(sample_idea)
    analysis = processor.analyse()
    assert analysis.word_count >= len(analysis.keywords)
    assert "echoevolver" in analysis.keywords
    assert analysis.sentiment in {"positive", "slightly_positive"}
    assert 0.0 < analysis.density <= 1.0
    assert 0.0 < analysis.complexity <= 1.0


def test_process_idea_deterministic_with_seed(sample_idea: str) -> None:
    result_one = process_idea(sample_idea, rng_seed=42)
    result_two = process_idea(sample_idea, rng_seed=42)
    assert result_one.creativity == result_two.creativity
    assert result_one.analysis.sentiment == "positive"
    payload = json.loads(result_one.to_json())
    assert payload["processed"] is True
    assert payload["analysis"]["density"] == pytest.approx(result_one.analysis.density)


def test_complexity_accounts_for_unique_short_tokens() -> None:
    idea = "sun sky sea air"
    analysis = IdeaProcessor(idea).analyse()

    assert analysis.keywords == []  # all tokens are shorter than four chars
    assert analysis.density == 0.0
    assert analysis.complexity > 0.0
    assert analysis.complexity <= 1.0

