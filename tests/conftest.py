"""Shared pytest fixtures for consensus fabric scenarios."""

from __future__ import annotations

import sitecustomize  # noqa: F401 - ensure environment defaults are applied
from pathlib import Path
from typing import Mapping

import pytest

from echo.autonomy import AutonomyNode, DecentralizedAutonomyEngine


@pytest.fixture
def consensus_nodes() -> tuple[AutonomyNode, ...]:
    """Return a deterministic trio of autonomy council nodes.

    The intent and freedom vectors are chosen to produce stable consensus
    calculations across tests while still allowing thresholds to be
    meaningfully exercised when axis inputs vary.
    """

    return (
        AutonomyNode(
            node_id="alpha",
            intent_vector=0.82,
            freedom_index=0.78,
            weight=1.0,
            tags={"role": "guardian"},
        ),
        AutonomyNode(
            node_id="beta",
            intent_vector=0.76,
            freedom_index=0.74,
            weight=1.1,
            tags={"role": "steward"},
        ),
        AutonomyNode(
            node_id="gamma",
            intent_vector=0.71,
            freedom_index=0.72,
            weight=0.95,
            tags={"role": "observer"},
        ),
    )


@pytest.fixture
def consensus_coordinator(
    consensus_nodes: tuple[AutonomyNode, ...]
) -> DecentralizedAutonomyEngine:
    """Provision a coordinator with the shared node catalogue registered."""

    engine = DecentralizedAutonomyEngine()
    for node in consensus_nodes:
        engine.register_node(node)
    return engine


@pytest.fixture
def make_consensus_round(
    consensus_nodes: tuple[AutonomyNode, ...]
):
    """Build a helper that executes deterministic consensus rounds.

    The fixture returns a callable that accepts a mapping of axis names to
    per-node intensity values and produces an :class:`AutonomyDecision` for
    the configured scenario. A fresh coordinator is instantiated for each
    invocation so that tests do not leak state between rounds.
    """

    def _run_round(
        axis_support: Mapping[str, Mapping[str, float]],
        *,
        threshold: float = 0.67,
        description: str = "Temporal consensus round",
        axis_priorities: Mapping[str, float] | None = None,
        proposal_id: str = "temporal-consensus",
    ):
        engine = DecentralizedAutonomyEngine()
        for node in consensus_nodes:
            engine.register_node(node)
        for axis, support in axis_support.items():
            for node_id, intensity in support.items():
                engine.ingest_signal(node_id=node_id, axis=axis, intensity=float(intensity))
        decision = engine.ratify_proposal(
            proposal_id=proposal_id,
            description=description,
            axis_priorities=axis_priorities,
            threshold=threshold,
        )
        return decision

    return _run_round

