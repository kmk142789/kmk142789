"""Tests for impact graph and forecasting."""

from __future__ import annotations

from echo.graph import ImpactGraph, build_graph, forecast_resonance


def test_build_graph_creates_digest():
    manifest = {
        "engines": [{"name": "EngineA", "module_spec": "echo.module:Engine"}],
        "states": {"cycle": 1, "resonance": 1.0, "amplification": 1.0, "snapshots": []},
        "kits": [{"name": "KitA", "path": "kits/kit"}],
    }
    graph = build_graph(manifest=manifest)
    assert graph.digest
    assert "manifest" in graph.nodes


def test_impacted_nodes_detects_related_paths():
    manifest = {
        "engines": [{"name": "EngineA", "module_spec": "echo.module:Engine"}],
        "states": {"cycle": 1, "resonance": 1.0, "amplification": 1.0, "snapshots": []},
        "kits": [],
    }
    graph = build_graph(manifest=manifest)
    impacted = graph.impacted_nodes(["echo/module.py"])
    assert "engines:EngineA" in impacted


def test_forecast_resonance_produces_scores():
    manifest = {
        "engines": [{"name": "EngineA", "module_spec": "echo.module:Engine"}],
        "states": {"cycle": 1, "resonance": 1.0, "amplification": 1.0, "snapshots": []},
        "kits": [],
    }
    graph = build_graph(manifest=manifest)
    forecast = forecast_resonance(graph, window="7d")
    assert set(forecast) == set(graph.nodes)
    for value in forecast.values():
        assert 0 <= value <= 2
