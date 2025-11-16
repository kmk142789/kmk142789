"""Tests for :mod:`echo.echo_genesis_core`."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from echo.echo_genesis_core import EchoGenesisCore, SubsystemProbe


@dataclass
class SequencedProbe:
    """Callable helper returning payloads in sequence."""

    payloads: Iterable[Mapping[str, float]]

    def __post_init__(self) -> None:
        self._payloads = list(self.payloads)
        self._index = 0

    def __call__(self) -> Mapping[str, float]:
        payload = self._payloads[self._index]
        if self._index < len(self._payloads) - 1:
            self._index += 1
        return payload


def build_genesis_core(tmp_path: Path) -> EchoGenesisCore:
    probes = [
        SubsystemProbe(
            name="quantum",
            kind="quantum",
            focus="entanglement",
            probe=SequencedProbe(
                [
                    {"signal": 0.92, "stability": 0.91},
                    {"signal": 0.55, "stability": 0.58},
                ]
            ),
            weight=1.0,
        ),
        SubsystemProbe(
            name="telemetry",
            kind="telemetry",
            focus="signal mesh",
            probe=SequencedProbe(
                [
                    {"signal": 0.68, "health": 0.64},
                    {"signal": 0.72, "health": 0.69},
                ]
            ),
        ),
        SubsystemProbe(
            name="orchestration",
            kind="orchestrator",
            focus="coordination",
            probe=SequencedProbe(
                [
                    {"coherence": 0.61},
                    {"coherence": 0.74},
                ]
            ),
        ),
        SubsystemProbe(
            name="analytics",
            kind="analytics",
            focus="insights",
            probe=SequencedProbe(
                [
                    {"score": 0.57},
                    {"score": 0.77},
                ]
            ),
        ),
        SubsystemProbe(
            name="governance",
            kind="governance",
            focus="policy",
            probe=SequencedProbe(
                [
                    {"compliance": 0.83},
                    {"compliance": 0.9},
                ]
            ),
        ),
    ]
    return EchoGenesisCore(probes=probes, state_dir=tmp_path / "genesis_state")


def test_echo_genesis_core_synthesizes_unified_state(tmp_path) -> None:
    core = build_genesis_core(tmp_path)
    state = core.synthesize()

    subsystems = state["architecture"]["subsystems"]
    assert set(subsystems) == {"quantum", "telemetry", "orchestration", "analytics", "governance"}
    assert state["refinement_index"] > 0
    assert state["self_refinement"]["analytics"]["mean_signal"] > 0
    assert core.latest_path.exists()


def test_echo_genesis_core_tracks_momentum_and_delta(tmp_path) -> None:
    core = build_genesis_core(tmp_path)
    first = core.synthesize()
    second = core.synthesize()

    momentum = second["self_refinement"]["momentum"]
    assert momentum["trend"] in {"accelerating", "regressing", "steady"}
    assert second["architecture"]["subsystems"]["quantum"]["delta"] != 0
    assert second["refinement_index"] != first["refinement_index"]


def test_from_components_wires_resonance_layer(tmp_path) -> None:
    class DummyLayer:
        def __init__(self) -> None:
            self.calls = 0

        def snapshot(self) -> Mapping[str, float]:
            self.calls += 1
            return {"signal": 0.81, "synchrony_index": 0.8}

    layer = DummyLayer()
    core = EchoGenesisCore.from_components(
        resonance_layer=layer,
        state_dir=tmp_path / "genesis_state",
    )

    state = core.synthesize()

    assert "resonance" in state["architecture"]["subsystems"]
    assert layer.calls == 1
