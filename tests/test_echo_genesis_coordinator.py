"""Tests for :mod:`echo.echo_genesis_coordinator`."""
from __future__ import annotations

from pathlib import Path

from echo.echo_genesis_core import EchoGenesisCore
from echo.echo_genesis_coordinator import EchoGenesisCoordinator


class DummySubsystem:
    """Return predefined payloads through a ``snapshot`` method."""

    def __init__(self, payloads: list[dict[str, float]]) -> None:
        self._payloads = payloads
        self._index = 0

    def snapshot(self) -> dict[str, float]:
        payload = self._payloads[self._index]
        if self._index < len(self._payloads) - 1:
            self._index += 1
        return payload


def build_coordinator(tmp_path: Path) -> EchoGenesisCoordinator:
    core = EchoGenesisCore(probes=[], state_dir=tmp_path / "genesis_state")
    coordinator = EchoGenesisCoordinator(core, state_dir=tmp_path / "coordinator_state")
    quantum = DummySubsystem([
        {"signal": 0.91, "stability": 0.9},
        {"signal": 0.86, "stability": 0.84},
    ])
    telemetry = DummySubsystem([
        {"signal": 0.72, "health": 0.7},
        {"signal": 0.75, "health": 0.73},
    ])
    coordinator.link_subsystem(
        "quantum",
        quantum,
        kind="quantum",
        focus="entanglement",
        metadata={"layer": "foundation"},
    )
    coordinator.link_subsystem(
        "telemetry",
        telemetry,
        kind="telemetry",
        focus="signal mesh",
        dependencies=("quantum",),
        metadata={"layer": "synthesis"},
    )
    return coordinator


def test_coordinator_cycle_builds_interaction_mesh(tmp_path: Path) -> None:
    coordinator = build_coordinator(tmp_path)
    state = coordinator.cycle()

    assert "architecture" in state
    assert state["coordination_index"] > 0
    mesh = state["interaction_mesh"]
    assert mesh["nodes"] == 2
    assert mesh["edges"] == [{"source": "telemetry", "target": "quantum"}]
    telemetry_state = state["subsystems"]["telemetry"]["state"]
    assert "linked_state" in telemetry_state
    assert "quantum" in telemetry_state["linked_state"]


def test_coordinator_snapshot_tracks_history_and_links(tmp_path: Path) -> None:
    coordinator = build_coordinator(tmp_path)
    cycle = coordinator.cycle()

    snapshot = coordinator.snapshot()
    assert "quantum" in snapshot["links"]
    assert snapshot["history"][0]["coordination_index"] == cycle["coordination_index"]
    assert Path(snapshot["state_path"]).exists()
    assert Path(snapshot["history_path"]).exists()
