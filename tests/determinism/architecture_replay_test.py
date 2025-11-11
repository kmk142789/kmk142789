"""Deterministic replay tests for the Hypernova architecture."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from packages.core.src.echo.hypernova import architecture as architecture_module
from packages.core.src.echo.hypernova.orchestrator import HypernovaOrchestrator, OrchestrationConfig
from packages.core.src.echo.hypernova.renderers import HypernovaJsonRenderer

FIXTURE_DIR = Path(__file__).parent / "fixtures"
ARCHITECTURE_GRAPH = Path("system_architecture/architecture.graph.json")


@pytest.fixture()
def deterministic_orchestrator() -> HypernovaOrchestrator:
    """Return an orchestrator seeded for deterministic output."""

    rng = architecture_module._RANDOM
    state = rng.getstate()
    rng.seed(int.from_bytes(b"ECHO", "big"))
    try:
        config = OrchestrationConfig(metadata={"generated_at": "2024-01-01T00:00:00Z"})
        orchestrator = HypernovaOrchestrator(config=config)
        orchestrator.build_blueprint()
        yield orchestrator
    finally:
        rng.setstate(state)


def _load_text(name: str) -> str:
    return (FIXTURE_DIR / name).read_text()


def _load_json(name: str) -> object:
    return json.loads((FIXTURE_DIR / name).read_text())


def _load_architecture_graph() -> object:
    return json.loads(ARCHITECTURE_GRAPH.read_text())


def test_hypernova_architecture_determinism(deterministic_orchestrator: HypernovaOrchestrator) -> None:
    orchestrator = deterministic_orchestrator
    blueprint = orchestrator.build_blueprint()

    assert blueprint.summary() == _load_text("hypernova_blueprint_summary.txt")
    assert orchestrator.render_ascii_map() == _load_text("hypernova_ascii_map.txt")
    assert orchestrator.render_text_registry() == _load_text("hypernova_text_registry.txt")
    assert json.loads(orchestrator.render_json_payload()) == _load_json("hypernova_json_payload.json")
    assert orchestrator.compose_artifact() == _load_json("hypernova_artifact.json")
    assert orchestrator.render_artifact_text() == _load_text("hypernova_artifact_text.md")

    renderer = HypernovaJsonRenderer(blueprint)
    generated_graph = json.loads(renderer.render())
    assert generated_graph == _load_architecture_graph()
