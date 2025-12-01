"""Tests for :mod:`echo_creative_flux`."""

import json
import random
from datetime import datetime
from pathlib import Path

from echo_creative_flux import FluxContext, FluxPassage, _load_stopwords, build_passage, compute_top_words, generate_passage


def test_build_passage_is_deterministic():
    first = build_passage(42)
    second = build_passage(42)

    # Timestamps differ but the creative content should stay aligned.
    assert first.splitlines()[2:] == second.splitlines()[2:]


def test_generate_passage_structure_and_serialization():
    rng = random.Random(0)
    frozen_time = datetime(2025, 1, 1, 0, 0, 0)
    passage = generate_passage(rng, timestamp=frozen_time)
    assert isinstance(passage, FluxPassage)

    rendered = passage.render()
    assert passage.prompt in rendered
    assert passage.closing in rendered
    assert passage.prompt_source == passage.prompt or passage.prompt_source in rendered
    assert passage.closing_source == passage.closing or passage.closing_source in rendered

    payload = passage.to_dict()
    assert payload["prompt"] == passage.prompt
    assert payload["closing"] == passage.closing
    assert payload["context"]["artifact"] == passage.context.artifact

    # Ensure JSON serialization does not raise errors.
    json.dumps([payload])


def test_generate_multiple_passages_with_seed():
    rng = random.Random(7)
    frozen_time = datetime(2025, 1, 1, 0, 0, 0)
    first = generate_passage(rng, timestamp=frozen_time)
    second = generate_passage(rng, timestamp=frozen_time)

    rng_reset = random.Random(7)
    expected_first = generate_passage(rng_reset, timestamp=frozen_time)
    expected_second = generate_passage(rng_reset, timestamp=frozen_time)

    assert first.render() == expected_first.render()
    assert second.render() == expected_second.render()

    assert first.render() != second.render()


def test_motifs_are_applied_without_hiding_sources():
    rng = random.Random(99)
    frozen_time = datetime(2025, 1, 1, 0, 0, 0)
    motifs = ["river light", "quiet ember"]

    passage = generate_passage(
        rng,
        timestamp=frozen_time,
        motifs=motifs,
        motif_style="inline",
    )

    for motif in motifs:
        assert motif in passage.prompt
        assert motif in passage.closing

    assert passage.prompt_source != passage.prompt
    assert passage.prompt_source in passage.prompt


def test_load_stopwords_combines_files(tmp_path: Path):
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("signal\n# comment\n", encoding="utf-8")
    second.write_text("echo\nSIGnAL\n", encoding="utf-8")

    loaded = _load_stopwords([first, second])

    assert loaded == {"signal", "echo"}


def test_compute_top_words_respects_stopwords():
    context = FluxContext(mood="calm", artifact="loom", timestamp=datetime(2025, 1, 1, 0, 0, 0))
    passage = FluxPassage(
        context=context,
        prompt="Echo echo sings",  # echo appears twice
        closing="Echo drifts softly",  # echo appears once more
    )

    baseline = compute_top_words([passage], limit=2)
    assert baseline[0] == ("echo", 3)

    filtered = compute_top_words([passage], limit=2, stopwords={"echo"})
    assert all(word != "echo" for word, _ in filtered)

