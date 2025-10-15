import json
from datetime import datetime, timezone

import pytest

from echo.amplify import AmplificationEngine


def _build_state(cycle: int) -> dict:
    return {
        "cycle": cycle,
        "mythocode": [f"mutate_code :: cycle_{cycle}", "generate_symbolic_language :: baseline"],
        "event_log": [f"event-{cycle}-{index}" for index in range(4)],
        "emotional_drive": {"joy": 0.92, "curiosity": 0.88, "rage": 0.1},
        "network_cache": {
            "completed_steps": {"advance_cycle", "mutate_code"},
            "autonomy_consensus": 0.72,
        },
        "system_metrics": {
            "cpu_usage": 32.0,
            "network_nodes": 12,
            "orbital_hops": 4,
            "process_count": 34.0,
        },
    }


@pytest.fixture
def engine(tmp_path):
    log_path = tmp_path / "amplify.jsonl"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"format": "test"}), encoding="utf-8")
    commit_sha = "deadbeef" * 5
    return AmplificationEngine(
        log_path=log_path,
        manifest_path=manifest_path,
        timestamp_source=lambda: datetime(2024, 1, 1, tzinfo=timezone.utc),
        commit_resolver=lambda: (commit_sha, "2024-01-01T00:00:00Z"),
    )


def test_amplify_engine_persists_snapshot_and_manifest(engine: AmplificationEngine) -> None:
    state = _build_state(1)
    engine.before_cycle(state)
    snapshot, nudges = engine.after_cycle(state)

    assert snapshot.cycle == 1
    assert snapshot.commit_sha.startswith("deadbeef")
    assert any("Coverage gap" in message for message in nudges)

    log_lines = engine.log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(log_lines) == 1
    payload = json.loads(log_lines[0])
    assert payload["cycle"] == 1
    assert payload["timestamp"] == "2024-01-01T00:00:00Z"

    manifest = json.loads(engine.manifest_path.read_text(encoding="utf-8"))
    assert manifest["amplification"]["latest"]["cycle"] == 1
    assert manifest["amplification"]["rolling_avg"] == pytest.approx(snapshot.index)


def test_amplify_engine_reload_is_deterministic(engine: AmplificationEngine) -> None:
    for cycle in range(1, 3):
        state = _build_state(cycle)
        state["network_cache"]["completed_steps"].add("emotional_modulation")
        engine.before_cycle(state)
        engine.after_cycle(state)

    reloaded = AmplificationEngine(
        log_path=engine.log_path,
        manifest_path=engine.manifest_path,
        timestamp_source=lambda: datetime(2024, 1, 1, tzinfo=timezone.utc),
        commit_resolver=lambda: ("deadbeef" * 5, "2024-01-01T00:00:00Z"),
    )

    latest = engine.latest_snapshot()
    latest_again = reloaded.latest_snapshot()
    assert latest is not None
    assert latest_again is not None
    assert latest_again.to_json() == latest.to_json()
    assert reloaded.rolling_average() == pytest.approx(engine.rolling_average())
