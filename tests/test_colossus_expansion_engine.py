from __future__ import annotations

import json
from pathlib import Path
import random

from echo.orchestrator import ColossusExpansionEngine, save_expansion_log


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
