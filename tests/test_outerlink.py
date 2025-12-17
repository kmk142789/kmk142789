import json

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


def test_emit_state_surfaces_offline_cache(tmp_path):
    config = SafeModeConfig(
        allowed_commands=["echo"],
        allowed_roots=[tmp_path],
        event_log=tmp_path / "events.log",
        offline_cache_dir=tmp_path / "cache",
    )
    offline_state = OfflineState(online=False)
    runtime = OuterLinkRuntime(config=config, offline_state=offline_state)

    runtime.safe_run_shell("echo", ["cache-me"])
    runtime.flush_events()

    state = runtime.emit_state()
    assert state["offline"]["cached_events"] == 1
    assert state["offline"]["pending_events"] == 0
    assert state["offline"]["online"] is False


def test_pending_events_drained_when_connection_recovers(tmp_path):
    config = SafeModeConfig(
        allowed_commands=["echo"],
        allowed_roots=[tmp_path],
        event_log=tmp_path / "events.log",
    )
    offline_state = OfflineState(online=False)
    runtime = OuterLinkRuntime(config=config, offline_state=offline_state)

    runtime.safe_run_shell("echo", ["queued"])
    runtime.offline_state.mark_online()
    runtime.flush_events()

    log_lines = config.event_log.read_text().splitlines()
    assert len(log_lines) == 1
    assert not runtime.offline_state.pending_events


def test_emit_state_carries_resilience_details(tmp_path):
    config = SafeModeConfig(
        allowed_commands=["echo"],
        allowed_roots=[tmp_path],
        event_log=tmp_path / "events.log",
        offline_cache_dir=tmp_path / "cache",
    )
    runtime = OuterLinkRuntime(config=config)

    state = runtime.emit_state()

    assert state["offline"].get("resilience_score") is not None
    assert runtime.offline_state.health_checks[-1]["name"] == "cache_health"


def test_offline_package_exports_integrity(tmp_path):
    config = SafeModeConfig(
        allowed_commands=["echo"],
        allowed_roots=[tmp_path],
        event_log=tmp_path / "events.log",
        offline_cache_dir=tmp_path / "cache",
    )
    offline_state = OfflineState(online=False)
    runtime = OuterLinkRuntime(config=config, offline_state=offline_state)

    runtime.safe_run_shell("echo", ["bundle"])
    runtime.flush_events()
    offline_state.record_health_check("radio_link", False, "antenna disabled")

    package_path = runtime.export_offline_state(tmp_path / "offline_package.json")
    package = json.loads(package_path.read_text())

    assert package["status"]["cached_events"] == 1
    assert package["health_checks"][-1]["name"] == "radio_link"
    assert package["integrity_hash"]


def test_offline_status_tracks_duration_and_integrity(tmp_path):
    config = SafeModeConfig(
        allowed_commands=["echo"],
        allowed_roots=[tmp_path],
        event_log=tmp_path / "events.log",
        offline_cache_dir=tmp_path / "cache",
    )
    offline_state = OfflineState(online=False)
    runtime = OuterLinkRuntime(config=config, offline_state=offline_state)

    runtime.safe_run_shell("echo", ["cache-me"])
    runtime.flush_events()

    offline_state.mark_offline("link_down")
    snapshot = offline_state.status(config.offline_cache_dir, config.offline_cache_ttl_seconds)

    assert snapshot["offline_since"] is not None
    assert snapshot["offline_duration_seconds"] is not None
    assert snapshot["cache_integrity"]["present"] is True
    assert snapshot["cache_integrity"]["files"] == 1
    assert snapshot["cache_integrity"]["hash"]


def test_backpressure_caps_pending_events(tmp_path):
    config = SafeModeConfig(
        allowed_commands=["echo"],
        allowed_roots=[tmp_path],
        pending_backlog_hard_limit=2,
    )
    offline_state = OfflineState(online=False)
    runtime = OuterLinkRuntime(config=config, offline_state=offline_state)

    runtime.safe_run_shell("echo", ["one"])
    runtime.safe_run_shell("echo", ["two"])
    runtime.safe_run_shell("echo", ["three"])

    state = runtime.emit_state()

    assert len(runtime.offline_state.pending_events) == 2
    assert state["offline"]["pending_events"] == 2
    assert any("backpressure limit" in note for note in runtime.offline_state.resilience_notes)


def test_backpressure_updates_capabilities(tmp_path):
    config = SafeModeConfig(
        allowed_commands=["echo"],
        allowed_roots=[tmp_path],
        pending_backlog_threshold=1,
    )
    offline_state = OfflineState(online=False)
    runtime = OuterLinkRuntime(config=config, offline_state=offline_state)

    runtime.safe_run_shell("echo", ["first"])
    runtime.safe_run_shell("echo", ["second"])

    runtime.emit_state()

    assert runtime.offline_state.offline_capabilities["backpressure_guardrails"] is False
    assert any(
        entry["name"] == "backpressure_guardrails" and entry["enabled"] is False
        for entry in runtime.offline_state.capability_history
    )


def test_emit_state_recommends_next_action(tmp_path):
    config = SafeModeConfig(
        allowed_commands=["echo"],
        allowed_roots=[tmp_path],
        pending_backlog_threshold=1,
        offline_cache_dir=tmp_path / "cache",
    )
    offline_state = OfflineState(online=False)
    runtime = OuterLinkRuntime(config=config, offline_state=offline_state)

    runtime.offline_state.pending_events.extend([
        {"name": "one"},
        {"name": "two"},
    ])

    state = runtime.emit_state()

    assert "resilience" in state
    assert "next_action" in state["resilience"]
    assert "backlog" in state["resilience"]["next_action"]


def test_emit_state_surfaces_backpressure_and_cache_window(tmp_path):
    config = SafeModeConfig(
        allowed_commands=["echo"],
        allowed_roots=[tmp_path],
        pending_backlog_threshold=1,
        pending_backlog_hard_limit=3,
        offline_cache_dir=tmp_path / "cache",
        offline_cache_ttl_seconds=10,
    )
    offline_state = OfflineState(online=False)
    runtime = OuterLinkRuntime(config=config, offline_state=offline_state)

    runtime.safe_run_shell("echo", ["one"])
    runtime.safe_run_shell("echo", ["two"])

    state = runtime.emit_state()

    backpressure = state["offline"]["backpressure"]
    cache_window = state["offline"]["cache_window"]

    assert backpressure["pending"] == 2
    assert backpressure["state"] == "elevated"
    assert cache_window["ttl_seconds"] == 10
    assert cache_window["stale"] is True


def test_emit_state_adds_stability_insights(tmp_path):
    config = SafeModeConfig(
        allowed_commands=["echo"],
        allowed_roots=[tmp_path],
        pending_backlog_threshold=1,
        offline_cache_dir=tmp_path / "cache",
    )
    offline_state = OfflineState(online=False)
    offline_state.mark_offline("link_down")
    runtime = OuterLinkRuntime(config=config, offline_state=offline_state)

    runtime.safe_run_shell("echo", ["offline-one"])
    runtime.safe_run_shell("echo", ["offline-two"])

    state = runtime.emit_state()
    stability = state["offline"].get("stability")

    assert stability is not None
    assert stability.get("stability_index") is not None
    assert stability.get("risk_signals"), "stability insights should flag active risks"
    assert stability.get("priority") in {"flush_backlog", "refresh_cache", "prepare_sync", "steady_state"}
    assert state["resilience"].get("stability") == stability


def test_event_history_enforces_retention_limit(tmp_path):
    config = SafeModeConfig(
        allowed_commands=["echo"],
        allowed_roots=[tmp_path],
        event_history_limit=3,
    )
    runtime = OuterLinkRuntime(config=config)

    for index in range(3):
        runtime.event_bus.emit("custom", {"i": index})

    stats_before = runtime.event_bus.stats()
    assert stats_before["retained"] == 3
    assert stats_before["dropped"] == 0

    state = runtime.emit_state()

    stats_after = runtime.event_bus.stats()
    assert stats_after["retained"] == 3
    assert stats_after["dropped"] == 1
    assert state["events"]["limit"] == 3
    assert state["events"]["dropped"] == 1
