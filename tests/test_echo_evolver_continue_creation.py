import random

import pytest

from echo.evolver import Eden88CreationStats, EchoEvolver


@pytest.fixture
def evolver(tmp_path):
    return EchoEvolver(rng=random.Random(3), artifact_path=tmp_path / "artifact.json")


def test_continue_creation_executes_creation_steps(evolver):
    payload = evolver.continue_creation(theme="aurora", persist_artifact=False)

    assert payload["decision"] == "continue_creation"
    assert payload["cycle"] == evolver.state.cycle == 1
    assert payload["executed_steps"][-1] == "eden88_create_artifact"

    creation = payload["creation"]
    assert creation is not None
    assert creation["theme"] == "aurora"

    digest = payload["digest"]
    assert digest["remaining_steps"][0] == "system_monitor"
    assert evolver.state.network_cache["continue_creation"]["creation"]["theme"] == "aurora"
    assert "Eden88 shaped" in payload["report"]

    stats = payload["creation_stats"]
    assert stats["total_creations"] == 1
    assert stats["theme_counts"]["aurora"] == 1
    assert stats["last_theme"] == "aurora"
    assert stats["streaks"]["current"]["length"] == 1
    assert stats["diversity"]["ratio"] == 1.0


def test_continue_creation_refreshes_existing_cycle(evolver):
    first = evolver.continue_creation(persist_artifact=False)

    second = evolver.continue_creation(theme="quantum", persist_artifact=False)

    assert second["decision"] == "continue_creation"
    assert second["cycle"] == evolver.state.cycle == first["cycle"]
    assert second["executed_steps"] == ["eden88_create_artifact"]
    assert second["creation"]["theme"] == "quantum"

    record = evolver.state.network_cache["continue_creation"]
    assert record["creation"]["theme"] == "quantum"
    stats = second["creation_stats"]
    assert stats["total_creations"] == 2
    assert stats["theme_counts"]["quantum"] >= 1
    assert stats["last_theme"] == "quantum"
    assert stats["streaks"]["current"]["theme"] == "quantum"
    assert 0 < stats["diversity"]["ratio"] <= 1.0


def test_eden88_creation_stats_balances_theme_selection():
    stats = Eden88CreationStats()

    stats.record_creation(
        {"cycle": 1, "theme": "aurora", "joy": 0.9, "curiosity": 0.95},
        timestamp_ns=1,
    )

    suggestion = stats.suggest_theme(["aurora", "quantum", "memory"], rng=random.Random(0))
    assert suggestion in {"quantum", "memory"}

    stats.record_creation(
        {"cycle": 2, "theme": suggestion, "joy": 0.92, "curiosity": 0.9},
        timestamp_ns=2,
    )

    summary = stats.snapshot()
    assert summary["total_creations"] == 2
    assert summary["unique_themes"] == 2
    assert summary["joy"]["max"] >= summary["joy"]["min"]
    assert summary["streaks"]["longest"]["length"] >= 1


def test_eden88_creation_stats_resets_streak_with_new_theme():
    stats = Eden88CreationStats()

    stats.record_creation({"cycle": 1, "theme": "aurora"}, timestamp_ns=1)
    stats.record_creation({"cycle": 2, "theme": "aurora"}, timestamp_ns=2)
    stats.record_creation({"cycle": 3, "theme": "memory"}, timestamp_ns=3)

    summary = stats.snapshot()
    assert summary["streaks"]["current"] == {"theme": "memory", "length": 1}
    assert summary["streaks"]["longest"]["theme"] == "aurora"
    assert summary["streaks"]["longest"]["length"] == 2


def test_summarise_eden88_creations_respects_recent_limit(evolver):
    evolver.continue_creation(theme="aurora", persist_artifact=False)
    evolver.continue_creation(theme="quantum", persist_artifact=False)
    evolver.continue_creation(theme="memory", persist_artifact=False)

    summary = evolver.summarise_eden88_creations(recent_limit=2)
    assert len(summary["recent_creations"]) == 2
    assert summary["total_creations"] == 3
