import json
import random
from pathlib import Path

import pytest

from echo import EchoAI, EchoResonanceEngine, HarmonicConfig, HarmonicsAI


def test_harmonics_resonance_adjustment() -> None:
    config = HarmonicConfig(expansion_threshold=1e6)
    harmonics = HarmonicsAI(config=config, rng=random.Random(42))

    response = harmonics.respond("Echo")

    assert "Symbolic refresh pending" in response.message
    assert response.pattern is None
    assert harmonics.chain_memory == []


def test_harmonics_expansion(tmp_path: Path) -> None:
    config = HarmonicConfig(expansion_threshold=0.1)
    harmonics = HarmonicsAI(config=config, rng=random.Random(7))

    response = harmonics.respond("Expand cognitive resonance")

    assert response.pattern is not None
    assert harmonics.chain_memory  # pattern stored
    assert response.harmonic_score > 0


def test_echo_ai_memory(tmp_path: Path) -> None:
    memory_file = tmp_path / "echo_memory.json"
    agent = EchoAI(memory_file=memory_file, rng=random.Random(11))

    reply = agent.respond("How are you feeling today?")

    assert "thriving" in reply
    data = json.loads(memory_file.read_text())
    assert data["conversations"][-1]["user"] == "How are you feeling today?"


def test_resonance_engine_process(tmp_path: Path) -> None:
    harmonics = HarmonicsAI(
        config=HarmonicConfig(expansion_threshold=0.1), rng=random.Random(99)
    )
    echo_agent = EchoAI(memory_file=tmp_path / "echo_memory.json", rng=random.Random(99))
    engine = EchoResonanceEngine(harmonics=harmonics, echo=echo_agent)

    result = engine.process("Expand cognitive resonance")

    assert "echo" in result and "harmonic_message" in result
    assert result["chain_memory"]
    assert result["harmonic_score"] > 0
    assert "resonance_trend" in result


def test_harmonics_resonance_trend_detects_growth() -> None:
    harmonics = HarmonicsAI(config=HarmonicConfig(expansion_threshold=10.0))
    harmonics.symbolic_matrix = {"a": 1.0, "b": 1.5, "c": 2.0}

    harmonics.respond("a")
    harmonics.respond("b")
    harmonics.respond("c")

    trend = harmonics.resonance_trend(window=3)
    history = harmonics.score_history[-3:]
    expected = (history[-1] - history[0]) / 2

    assert trend == pytest.approx(expected, rel=1e-6)
    assert trend > 0


def test_harmonics_resonance_trend_requires_window() -> None:
    harmonics = HarmonicsAI()

    with pytest.raises(ValueError):
        harmonics.resonance_trend(window=1)

    assert harmonics.resonance_trend(window=3) == 0.0
