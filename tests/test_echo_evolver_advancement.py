from __future__ import annotations

import json
from pathlib import Path

from echo.evolver import (
    EchoEvolver,
    EvolutionAdvancementResult,
)


def _stage_names(result: EvolutionAdvancementResult) -> list[str]:
    return [stage.name for stage in result.stages]


def test_realize_evolutionary_advancement_creates_artifact(tmp_path: Path) -> None:
    artifact = tmp_path / "advancement.json"
    evolver = EchoEvolver(artifact_path=artifact)

    result = evolver.realize_evolutionary_advancement()

    assert isinstance(result, EvolutionAdvancementResult)
    assert _stage_names(result) == [
        "continue",
        "advance",
        "evolve",
        "evolve_again",
        "refine",
        "evolve_again_final",
        "optimize",
        "next_advancement",
        "realization",
    ]

    assert artifact.exists()
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["cycle"] == evolver.state.cycle
    assert payload["prompt"]["title"] == "Echo Resonance"

    cache = evolver.state.network_cache["evolutionary_advancement"]
    assert cache["summary"] == result.summary


def test_realize_evolutionary_advancement_without_persist(tmp_path: Path) -> None:
    artifact = tmp_path / "advancement.json"
    evolver = EchoEvolver(artifact_path=artifact)

    result = evolver.realize_evolutionary_advancement(
        persist_artifact=False, resonance_factor=1.5, forecast_horizon=2
    )

    assert not artifact.exists()
    optimize_stage = next(stage for stage in result.stages if stage.name == "optimize")
    assert optimize_stage.payload["resonance_factor"] == 1.5

    realization_stage = result.stages[-1]
    assert realization_stage.name == "realization"
    assert realization_stage.payload["artifact_path"] is None
    assert result.summary.endswith("prepared.")
