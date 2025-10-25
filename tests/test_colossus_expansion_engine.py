from __future__ import annotations

import json
from pathlib import Path
import random

from echo.orchestrator import (
    ColossusExpansionEngine,
    CosmosEngine,
    save_expansion_log,
)


def _engine(tmp_path: Path) -> ColossusExpansionEngine:
    rng = random.Random(0)
    return ColossusExpansionEngine(
        state_dir=tmp_path / "state",
        cycle_size=10,
        time_source=lambda: 1234567890.123456,
        rng=rng,
    )


def test_generate_cycle_shapes(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    artifacts = engine.generate_cycle(0)
    assert len(artifacts) == 10
    first = artifacts[0]
    assert first["type"] == "puzzle"
    assert first["echo"] == "∇⊸≋∇"
    assert first["payload"]["script"].startswith("OP_DUP OP_HASH160")


def test_run_persists_cycles(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    log = engine.run(2)
    assert len(log) == 2
    cycle_path = engine.state_directory / "cycle_00000.json"
    assert cycle_path.exists()
    data = json.loads(cycle_path.read_text(encoding="utf-8"))
    assert data["cycle"] == 0
    assert len(data["artifacts"]) == 10


def test_save_expansion_log(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    cycles = engine.run(1)
    log_path = tmp_path / "colossus_log.json"
    save_expansion_log(log_path, cycles)
    saved = json.loads(log_path.read_text(encoding="utf-8"))
    assert len(saved) == 1
    assert saved[0][0]["id"].startswith("COLOSSUS_0_0")


def test_cosmos_fabricator_entangles_universes(tmp_path: Path) -> None:
    cosmos = CosmosEngine(
        state_dir=tmp_path / "cosmos",
        cycle_size=4,
        time_source=lambda: 42.0,
        rng=random.Random(1234),
    )
    fabrication = cosmos.cosmos_fabricator(["alpha", "beta"], cycles=1)
    assert set(fabrication.universes) == {"alpha", "beta"}
    assert len(fabrication.entanglement) == 4
    key = "0:0"
    entangled = fabrication.entanglement[key]
    assert set(entangled) == {"alpha", "beta"}
    alpha_artifact = fabrication.universes["alpha"].artifact(0, 0)
    beta_artifact = fabrication.universes["beta"].artifact(0, 0)
    assert entangled["alpha"] == alpha_artifact["id"]
    assert (
        fabrication.universes["alpha"].entangled_lineage[alpha_artifact["id"]]["beta"]
        == beta_artifact["id"]
    )
    assert fabrication.universes["alpha"].entropy != ""
    assert fabrication.universes["alpha"].state_signature != ""


def test_cosmos_explorer_filters_by_predicate(tmp_path: Path) -> None:
    cosmos = CosmosEngine(
        state_dir=tmp_path / "cosmos",
        cycle_size=4,
        time_source=lambda: 77.0,
        rng=random.Random(4321),
    )
    fabrication = cosmos.cosmos_fabricator(["alpha", "beta"], cycles=1)
    lineage_records = cosmos.cosmos_explorer(
        fabrication,
        universes=["alpha"],
        predicate=lambda artifact: artifact["type"] == "lineage",
    )
    assert lineage_records
    assert all(record["cosmos"] == "alpha" for record in lineage_records)
    assert all(record["type"] == "lineage" for record in lineage_records)


def test_cosmos_verification_reports_divergence(tmp_path: Path) -> None:
    cosmos = CosmosEngine(
        state_dir=tmp_path / "cosmos",
        cycle_size=3,
        time_source=lambda: 11.0,
        rng=random.Random(9999),
    )
    fabrication = cosmos.cosmos_fabricator(["alpha", "beta"], cycles=1)
    report = fabrication.verification
    assert set(report) == {"agreements", "divergences"}
    assert isinstance(report["agreements"], list)
    assert isinstance(report["divergences"], list)
    assert report["divergences"]
    divergence = report["divergences"][0]
    assert "merged_payload" in divergence
    assert set(divergence["merged_payload"]["universes"]) == {"alpha", "beta"}
    refreshed = cosmos.verification_layer(fabrication)
    assert refreshed == fabrication.verification
