import pytest

from outerlink import OuterLinkRuntime, SafeModeConfig, OfflineState, ExecutionBroker, DeviceSurfaceInterface, EventBus


def test_runtime_emits_device_status(tmp_path):
    config = SafeModeConfig(allowed_roots=[tmp_path])
    runtime = OuterLinkRuntime(config=config)
    state = runtime.emit_state()

    assert "metrics" in state
    assert runtime.event_bus.history[-1].name == "device_status"


def test_router_offline_fallback():
    offline_state = OfflineState(online=False)
    runtime = OuterLinkRuntime(offline_state=offline_state)
    decision = runtime.router.route("unknown_task")

    assert decision.fallback_used is True
    assert decision.target == "offline_fallback"


def test_broker_blocks_disallowed_command(tmp_path):
    config = SafeModeConfig(allowed_commands=["echo"], allowed_roots=[tmp_path])
    runtime = OuterLinkRuntime(config=config)
    with pytest.raises(PermissionError):
        runtime.safe_run_shell("ls")


def test_broker_records_pending_when_offline(tmp_path):
    offline_state = OfflineState(online=False)
    config = SafeModeConfig(allowed_commands=["echo"], allowed_roots=[tmp_path])
    dsi = DeviceSurfaceInterface(config)
    broker = ExecutionBroker(config, dsi, EventBus(), offline_state)

    result = broker.run_shell("echo", ["hello"])
    assert result.returncode == 0
    assert offline_state.pending_events, "Event should be buffered while offline"


def test_offline_cache_restored_when_online(tmp_path):
    config = SafeModeConfig(
        allowed_commands=["echo"],
        allowed_roots=[tmp_path],
        event_log=tmp_path / "events.log",
        offline_cache_dir=tmp_path / "cache",
    )
    offline_state = OfflineState(online=False)
    runtime = OuterLinkRuntime(config=config, offline_state=offline_state)

    runtime.safe_run_shell("echo", ["hi"])
    runtime.flush_events()

    cached = list(config.offline_cache_dir.glob("event_*.json"))
    assert cached, "Offline events should be cached to disk"

    runtime.offline_state.online = True
    runtime.flush_events()

    log_lines = config.event_log.read_text().splitlines()
    assert len(log_lines) == 1, "Cached events should be replayed once when online"
    assert not list(config.offline_cache_dir.glob("event_*.json")), "Cache should be cleared after replay"
    assert runtime.offline_state.last_sync is not None


def test_dsi_sensor_stub(tmp_path):
    config = SafeModeConfig(allowed_roots=[tmp_path])
    dsi = DeviceSurfaceInterface(config)
    reading = dsi.get_sensor("accelerometer")

    assert reading.name == "accelerometer"
    assert "x" in reading.value
