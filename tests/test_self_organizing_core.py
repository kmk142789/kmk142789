from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys


def _load_core_module():
    module_path = Path(__file__).resolve().parents[1] / "packages/core/src/echo/self_organizing_core.py"
    spec = spec_from_file_location("_echo_self_core", module_path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive branch
        raise RuntimeError("unable to load self_organizing_core module")
    module = module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


_core_module = _load_core_module()
SelfOrganizingCore = _core_module.SelfOrganizingCore
SubsystemAdapter = _core_module.SubsystemAdapter


def test_coordinate_builds_plan_and_persists(tmp_path: Path) -> None:
    adapters = [
        SubsystemAdapter(
            name="EchoShell",
            kind="interface",
            intent="monitoring",
            observe=lambda: {"progress": 0.7, "status": "ready"},
            priority=0.9,
        ),
        SubsystemAdapter(
            name="Eden88",
            kind="intelligence",
            intent="learning",
            observe=lambda: {"coherence": 0.5, "issues": []},
            priority=0.8,
        ),
    ]
    core = SelfOrganizingCore(subsystems=adapters, state_dir=tmp_path)
    plan = core.coordinate()

    assert len(plan.subsystems) == 2
    assert plan.network["nodes"][0]["id"] == "EchoShell"
    assert plan.priorities[0]["name"] in {"EchoShell", "Eden88"}
    assert (tmp_path / "plan_latest.json").exists()

    persisted = json.loads((tmp_path / "plan_latest.json").read_text())
    assert persisted["autonomy_score"] == plan.autonomy_score


def test_from_components_registers_available_subsystems(tmp_path: Path) -> None:
    class DummyEvolver:
        def cycle_digest(self, *, persist_artifact: bool) -> dict:
            return {"progress": 0.4, "cycle": 12, "next_step": "sync"}

    class DummyLoop:
        def __init__(self) -> None:
            self.state = {"current_cycle": 10}

    class DummyOrchestrator:
        latest_decision = None

        def orchestrate(self) -> dict:
            return {"coherence": {"score": 1000}, "inputs": {"cycle_digest": {"progress": 0.6}}}

    core = SelfOrganizingCore.from_components(
        evolver=DummyEvolver(),
        orchestrator=DummyOrchestrator(),
        loop=DummyLoop(),
        state_dir=tmp_path,
    )

    assert len(core.subsystems) == 3
    plan = core.coordinate()
    names = {snapshot.name for snapshot in plan.subsystems}
    assert {"EchoEvolver", "Orchestrator", "SelfSustainingLoop"} <= names
