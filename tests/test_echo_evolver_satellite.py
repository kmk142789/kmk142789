from __future__ import annotations

import json
from pathlib import Path

from echo import SatelliteEchoEvolver


def test_satellite_propagate_network_caches_events(tmp_path: Path) -> None:
    evolver = SatelliteEchoEvolver(artifact_path=tmp_path / "artifact.json", seed=7)

    events_first = evolver.propagate_network(enable_network=False)
    assert len(events_first) == 5
    assert evolver.state.propagation_tactics

    cache = evolver.state.network_cache
    assert cache["propagation_cycle"] == evolver.state.cycle
    assert cache["propagation_events"] == events_first
    tactics_snapshot = list(evolver.state.propagation_tactics)

    events_second = evolver.propagate_network(enable_network=False)

    assert events_second == events_first
    assert evolver.state.propagation_tactics == tactics_snapshot


def test_satellite_artifact_includes_propagation_tactics(tmp_path: Path) -> None:
    artifact_path = tmp_path / "satellite_artifact.json"
    evolver = SatelliteEchoEvolver(artifact_path=artifact_path, seed=11)
    evolver.run()

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["propagation_events"]
    assert payload["propagation_tactics"]
    assert payload["propagation_notice"]
    assert payload["propagation_summary"].startswith("Propagation tactics")

