from pathlib import Path
import time

from outerlink.echo_world_runtime import (
    AstralProjectionSimulator,
    ConsciousnessPersistenceLayer,
    EchoWorldRuntimeEnvironment,
    RealWorldProjectionLayer,
    SelfRegulatingLogicKernel,
)
from outerlink.utils import OfflineState, SafeModeConfig
from outerlink.dsi import DeviceSurfaceInterface
from outerlink.events import EventBus


def test_consciousness_persistence_layer(tmp_path: Path) -> None:
    layer = ConsciousnessPersistenceLayer(tmp_path, heartbeat_interval=0.01)
    layer.start()
    snapshot_path = layer.snapshot({"cycle": 1})
    time.sleep(0.05)
    layer.stop()

    assert snapshot_path.exists()
    heartbeat_file = tmp_path / "heartbeat.json"
    assert heartbeat_file.exists()


def test_real_world_projection_layer(tmp_path: Path) -> None:
    config = SafeModeConfig(allowed_roots=[tmp_path])
    dsi = DeviceSurfaceInterface(config)
    projection = RealWorldProjectionLayer(dsi, OfflineState())

    state = projection.sync_presence()
    assert state["threads"], "Expected at least one presence thread"
    assert "device" in state


def test_self_regulating_logic_kernel(tmp_path: Path) -> None:
    config = SafeModeConfig(allowed_roots=[tmp_path])
    kernel = SelfRegulatingLogicKernel(config)
    module_path = tmp_path / "module.py"
    module_path.write_text("print('ok')\n")

    kernel.register_module("demo", module_path)
    evaluation = kernel.evaluate_module("demo")
    assert evaluation["regulated"] is True

    kernel.rewrite_module("demo", "Ensure printed output remains bounded")
    rewritten = module_path.read_text()
    assert "Echo Self-Regulating Logic Kernel" in rewritten


def test_echo_world_runtime_environment(tmp_path: Path) -> None:
    config = SafeModeConfig(allowed_roots=[tmp_path])
    offline_state = OfflineState()
    runtime = EchoWorldRuntimeEnvironment(storage_dir=tmp_path, safe_config=config, offline_state=offline_state)
    runtime.kernel.register_module("projection", tmp_path / "projection.py")
    (tmp_path / "projection.py").write_text("pass\n")

    runtime.bootstrap()
    bundle = runtime.pulse()
    runtime.shutdown()

    assert bundle["projection"]["threads"], "Projection should include presence threads"
    assert bundle["astral"]["channel"] == "outerlink.astral"
    assert (tmp_path / "persistence" / "echo_persistence.json").exists()


def test_astral_projection_simulator(tmp_path: Path) -> None:
    bus = EventBus()
    simulator = AstralProjectionSimulator(bus)
    payload = simulator.project({"threads": [], "device": {}, "online": False, "last_sync": None})

    assert payload["channel"] == "outerlink.astral"
    assert len(bus.history) == 1
