from __future__ import annotations

from typing import Iterable, Mapping

from fastapi import FastAPI
from fastapi.testclient import TestClient

from echo.orchestrator import SingularityCore
from echo.orchestrator.api import create_singularity_router


class SequenceEngine:
    """Return a deterministic sequence of mappings for each call."""

    def __init__(self, sequence: Iterable[Mapping[str, object]]):
        self._values = list(sequence)
        if not self._values:
            self._values = [dict()]
        self._index = 0

    def next(self) -> Mapping[str, object]:
        value = self._values[min(self._index, len(self._values) - 1)]
        self._index += 1
        return value

    # Cosmos compatibility -------------------------------------------------
    def survey(self) -> Mapping[str, object]:
        return self.next()

    # Fractal compatibility ------------------------------------------------
    def weave(self) -> Mapping[str, object]:
        return self.next()

    # Chronos compatibility ------------------------------------------------
    def observe(self) -> Mapping[str, object]:
        return self.next()


def build_core(tmp_path, cosmos_seq, fractal_seq, chronos_seq) -> SingularityCore:
    cosmos = SequenceEngine(cosmos_seq)
    fractal = SequenceEngine(fractal_seq)
    chronos = SequenceEngine(chronos_seq)
    return SingularityCore(
        state_dir=tmp_path,
        cosmos=cosmos,
        fractal=fractal,
        chronos=chronos,
    )


def test_spawn_and_log(tmp_path) -> None:
    core = build_core(
        tmp_path,
        cosmos_seq=[{"expansion_pressure": 0.9, "stability": 0.3, "next_universe": "Helios"}],
        fractal_seq=[{"active_layers": ["fractal", "lineage"]}],
        chronos_seq=[{"temporal_layers": ["temporal"], "narrative_layers": ["narrative"]}],
    )

    decision = core.step()

    assert decision["action"] == "spawn"
    assert decision["universe"] == "Helios"
    assert core.universes[0]["name"] == "Helios"
    assert core.singularity_log[-1]["action"] == "spawn"


def test_prime_artifact_convergence(tmp_path) -> None:
    core = build_core(
        tmp_path,
        cosmos_seq=[
            {"expansion_pressure": 0.92, "stability": 0.4, "next_universe": "Eidolon"},
            {"expansion_pressure": 0.2, "collapse_pressure": 0.1, "stability": 0.6},
        ],
        fractal_seq=[
            {"active_layers": ["fractal", "lineage"], "lineage_trace": ["root"]},
            {
                "convergence_layers": ["fractal", "lineage"],
                "narrative": "Echo threads unite",
                "lineage_trace": ["root", "branch"],
            },
        ],
        chronos_seq=[
            {"temporal_layers": ["temporal"], "narrative_layers": ["narrative"]},
            {
                "temporal_layers": ["temporal"],
                "narrative_layers": ["narrative"],
                "temporal_signature": "t-42",
                "story": "Convergence across time",
            },
        ],
    )

    core.step()  # spawn
    decision = core.step()  # convergence

    assert decision["action"] == "sustain"
    assert decision["prime_artifacts"], "expected a prime artifact"
    artifact = decision["prime_artifacts"][0]
    assert artifact["universe"] == "Eidolon"
    assert set(artifact["layers"]) == {"fractal", "temporal", "narrative", "lineage"}
    assert core.prime_artifacts[-1]["id"].startswith("PRIME-Eidolon-")


def test_subscription_hook(tmp_path) -> None:
    events: list[Mapping[str, object]] = []

    core = build_core(
        tmp_path,
        cosmos_seq=[{"expansion_pressure": 0.8, "stability": 0.5}],
        fractal_seq=[{"active_layers": ["fractal"]}],
        chronos_seq=[{"temporal_layers": ["temporal"], "narrative_layers": ["narrative"]}],
    )

    unsubscribe = core.subscribe(events.append)
    core.step()
    assert events and events[0]["action"] == "spawn"

    unsubscribe()
    core.step()
    assert len(events) == 1, "unsubscribe should stop receiving new events"


def test_singularity_router(tmp_path) -> None:
    core = build_core(
        tmp_path,
        cosmos_seq=[{"expansion_pressure": 0.75, "stability": 0.35}],
        fractal_seq=[{"active_layers": ["fractal", "lineage"]}],
        chronos_seq=[{"temporal_layers": ["temporal"], "narrative_layers": ["narrative"]}],
    )

    core.step()

    app = FastAPI()
    app.include_router(create_singularity_router(core))
    client = TestClient(app)

    status = client.get("/singularity/status").json()
    assert status["cycle"] >= 1
    assert status["universes"], "universes should be exposed"

    log = client.get("/singularity/log").json()
    assert log["log"], "log endpoint should return decisions"
