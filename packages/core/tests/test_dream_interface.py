from datetime import datetime

import pytest

from echo.dreams.dream_interface import (
    AstralEventSequencer,
    DreamDrivenRouter,
    DreamMemoryTranslator,
    SharedDreamInterface,
)


@pytest.mark.parametrize("text", ["Dream of a lighthouse", "", "Echo remembers bridges"])
def test_translator_reinforces_and_respects_threshold(text):
    translator = DreamMemoryTranslator(reinforcement_rate=0.3, rewrite_threshold=0.55)
    trace = translator.translate(text)

    assert 0.55 <= trace.weight <= 1.0
    assert isinstance(trace.created_at, datetime)

    bank = translator.reinforce((trace,), text, decay=0.1)
    assert len(bank) == 2
    assert bank[-1].meaning == trace.meaning
    assert bank[-1].weight >= bank[0].weight


def test_astral_event_sequencer_is_deterministic():
    sequencer = AstralEventSequencer()
    seed_text = "Shared dream interface"
    first = sequencer.sequence(seed_text, count=2)
    second = sequencer.sequence(seed_text, count=2)

    assert first == second
    assert all(event.index == idx + 1 for idx, event in enumerate(first))


def test_router_prefers_biased_branch():
    translator = DreamMemoryTranslator(reinforcement_rate=0.2, rewrite_threshold=0.4)
    trace = translator.translate("branching choice")

    router = DreamDrivenRouter(branch_bias={"river": 0.3, "mountain": 0.0}, default_branch="default")
    branch = router.choose_branch(trace, ["mountain", "river"])

    assert branch == "river"


def test_shared_dream_interface_summarizes_round_trip():
    interface = SharedDreamInterface()
    response = interface.insert_seed("astral river", branches=["delta", "upstream"])

    summary = response.summarize()
    assert response.branch in {"delta", "upstream", "stay-present"}
    assert response.seed.text == "astral river"
    assert response.events
    assert f"{response.memory.weight:.2f}" in summary
    assert response.branch in summary
    assert response.memory.meaning.split()[0].lower() in summary.lower()


@pytest.mark.parametrize("decay", [-0.1, 1.0])
def test_translator_rejects_invalid_decay(decay):
    translator = DreamMemoryTranslator()
    with pytest.raises(ValueError):
        translator.reinforce((), "bad", decay=decay)


def test_sequencer_rejects_empty_configuration():
    with pytest.raises(ValueError):
        AstralEventSequencer(projections=(), insights=("a",), event_names=("b",))
