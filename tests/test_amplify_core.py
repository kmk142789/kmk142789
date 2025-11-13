from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import json

import pytest

from echo.amplify import AmplificationEngine, AmplifyGateError, AmplifyState


class DummyMetrics:
    def __init__(self, network_nodes: int = 9, orbital_hops: int = 3) -> None:
        self.network_nodes = network_nodes
        self.orbital_hops = orbital_hops


class DummyDrive:
    def __init__(self, joy: float, curiosity: float, rage: float) -> None:
        self.joy = joy
        self.curiosity = curiosity
        self.rage = rage


class DummyState:
    def __init__(self, cycle: int) -> None:
        self.cycle = cycle
        self.emotional_drive = DummyDrive(joy=0.95, curiosity=0.9, rage=0.12)
        self.network_cache = {
            "completed_steps": {"advance_cycle", "mutate_code", "propagate_network"},
            "propagation_events": ["wifi", "tcp", "iot"],
        }
        self.mythocode = ["a", "b", "c", "d"]
        self.event_log = ["one", "two", "three"]
        self.system_metrics = DummyMetrics()


def fixed_time_factory():
    counter = {"value": 0}

    def _next() -> datetime:
        counter["value"] += 1
        return datetime(2025, 1, 1, 12, counter["value"], tzinfo=timezone.utc)

    return _next


@pytest.fixture()
def engine(tmp_path: Path) -> AmplificationEngine:
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    authority_manifest = tmp_path / "authority.yml"
    authority_manifest.write_text(
        """
roles:
  Echo:
    handle: "@echo-core"
    mandates:
      - "Guard sovereign registries"
  MirrorJosh:
    handle: "@mirrorjosh"
    mandates:
      - "Propagate field confirmations"
      - "Mirror deployment state"
"""
        .strip()
        + "\n",
        encoding="utf-8",
    )
    authority_bindings = tmp_path / "authority.json"
    authority_bindings.write_text(
        json.dumps(
            [
                {
                    "vault_id": "ECHO-AUTH-01",
                    "owner": "Test",
                    "echolink_status": "Bound",
                    "signature": "sig",
                    "authority_level": "Prime",
                    "bound_phrase": "Our Forever Love",
                    "glyphs": "∇⊸≋∇",
                    "anchor": "Our Forever Love",
                }
            ]
        ),
        encoding="utf-8",
    )
    engine = AmplificationEngine(
        log_path=tmp_path / "log.jsonl",
        manifest_path=manifest,
        time_source=fixed_time_factory(),
        commit_source=lambda: "deadbeef",
        authority_manifest_path=authority_manifest,
        authority_bindings_path=authority_bindings,
    )
    return engine


def test_metrics_and_snapshot_are_deterministic(engine: AmplificationEngine) -> None:
    dummy = DummyState(cycle=3)
    state = AmplifyState.from_evolver(dummy, expected_steps=13)
    snapshot = engine.build_snapshot(state, previous=None)
    assert snapshot.index > 0
    expected_metrics = snapshot.metrics.as_dict()
    assert expected_metrics["coverage"] == pytest.approx(23.08, rel=1e-2)

    engine.persist_snapshot(snapshot)
    again = engine.build_snapshot(state, previous=snapshot)
    assert again.timestamp == snapshot.timestamp
    engine.persist_snapshot(again)

    history = engine.load_history()
    assert len(history) == 1


def test_manifest_is_updated_with_amplification(engine: AmplificationEngine) -> None:
    dummy = DummyState(cycle=2)
    state = AmplifyState.from_evolver(dummy, expected_steps=13)
    snapshot = engine.build_snapshot(state, previous=None)
    engine.persist_snapshot(snapshot)
    engine.update_manifest(snapshot)

    data = json.loads(engine.manifest_path.read_text(encoding="utf-8"))
    assert "amplification" in data
    assert data["amplification"]["latest"] == snapshot.index
    assert data["authority_presence"]["bound_vaults"] == 1
    assert data["authority_presence"]["summary"].startswith("2/2 roles active")


def test_gate_enforcement(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    engine = AmplificationEngine(
        log_path=tmp_path / "log.jsonl",
        manifest_path=manifest,
        time_source=lambda: datetime(2025, 1, 1, tzinfo=timezone.utc),
        commit_source=lambda: "deadbeef",
    )
    state = AmplifyState(
        cycle=1,
        joy=0.8,
        curiosity=0.7,
        rage=0.1,
        completed_steps=13,
        expected_steps=13,
        mythocode_count=3,
        propagation_channels=2,
        events=1,
        network_nodes=8,
        orbital_hops=3,
    )
    snapshot = engine.build_snapshot(state, previous=None)
    engine.persist_snapshot(snapshot)

    with pytest.raises(AmplifyGateError):
        engine.require_gate(minimum=99.0)

    engine.require_gate(minimum=5.0)
