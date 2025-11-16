"""Tests for :mod:`echo_creative_flux`."""

import json
import random
from datetime import datetime

from echo_creative_flux import FluxPassage, build_passage, generate_passage


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

