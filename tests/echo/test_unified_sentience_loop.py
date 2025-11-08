from __future__ import annotations

import json
from pathlib import Path

import pytest

from echo.unified_sentience_loop import UnifiedSentienceLoop


class DummyKernel:
    """Simple kernel stub that tracks invocations."""

    def __init__(self, pulse_path: Path, *, events: int = 3) -> None:
        self.pulse_path = pulse_path
        self.history = [object()] * events

    def resonance(self) -> str:
        return "stub-resonance"


class DummyOrchestrator:
    def __init__(self, manifest_directory: Path) -> None:
        self.latest_decision = {"id": "manifest-001", "status": "ok"}
        self.manifest_directory = manifest_directory


def test_progress_emits_metrics_and_status(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_payload = {
        "progress_actor": "loop-dev",
        "governance_actor": "council-dev",
        "pulse_history": "observability/pulse.json",
        "metrics_window": 4,
    }
    (config_dir / "dev.json").write_text(json.dumps(config_payload), encoding="utf-8")

    created_paths: list[Path] = []

    def kernel_factory(pulse_path: Path) -> DummyKernel:
        created_paths.append(pulse_path)
        return DummyKernel(pulse_path, events=2)

    manifest_directory = tmp_path / "manifests"
    orchestrator = DummyOrchestrator(manifest_directory)

    metrics_calls: list[tuple] = []
    governance_calls: list = []

    loop = UnifiedSentienceLoop.from_environment(
        tmp_path,
        "dev",
        config_dir=config_dir,
        orchestrator=orchestrator,
        metrics_reporters=[lambda progress, metrics: metrics_calls.append((progress, metrics))],
        governance_hooks=[governance_calls.append],
        kernel_factory=kernel_factory,
    )

    result = loop.progress("Completed orchestration bootstrap")
    assert result.cycle == 1
    expected_pulse_path = tmp_path / "observability" / "pulse.json"
    assert created_paths and all(path == expected_pulse_path for path in created_paths)

    state_path = tmp_path / "state" / "self_sustaining_loop.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["history"][0]["actor"] == "loop-dev"

    assert len(metrics_calls) == 1
    metrics = metrics_calls[0][1]
    assert metrics["pulse"] == {"events": 2, "resonance": "stub-resonance", "status": "ok"}
    assert metrics["orchestration"]["manifest_directory"] == str(manifest_directory)

    decision = loop.decide("cycle_0001", "approve")
    assert decision.status == "approved"
    assert len(governance_calls) == 1

    proposal_path = tmp_path / "state" / "proposals" / "cycle_0001.json"
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    assert proposal["governance"]["decider"] == "council-dev"

    report = loop.status_report()
    assert report["profile"] == "dev"
    assert report["pulse"]["status"] == "ok"
    assert report["loop"]["active_proposal"]["status"] == "approved"
    assert report["orchestration"]["latest"] == orchestrator.latest_decision


def test_missing_profile_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        UnifiedSentienceLoop.from_environment(tmp_path, "does-not-exist")
