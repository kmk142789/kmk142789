"""Hypernova world-building engine inside the :mod:`echo` universe.

This package assembles a sprawling, multi-layer simulation fabric that can be
used by tests, demos, or command-line utilities to craft elaborate mythic
structures.  Each module exposes a slice of the system:

``architecture``
    Core dataclasses that model nodes, conduits, domains, and energy flows.

``saga``
    Narrative generators that weave the architectural data into story beats.

``renderers``
    Presentation helpers that map structures into textual, JSON, and
    heat-map formats.

``orchestrator``
    Coordinating façade that drives the architecture builders, story engines,
    and renderers to produce complete artifacts in a single call.

``symphony``
    High-level musical metaphor utilities that express the hypernova in
    melodic terms for interactive experiences.

All modules are intentionally independent so downstream projects can either
use the orchestrator to generate an entire universe or cherry-pick specific
helpers for custom pipelines.
"""

from __future__ import annotations

from .architecture import (
    AstroConduit,
    ChronicleIndex,
    ContinuumDomain,
    EchoHypernode,
    HyperCelestialMatrix,
    HypernovaBlueprint,
    HyperpulseStream,
    MythicStratum,
    ResonantGlyph,
    ResonantSignature,
)
from .orchestrator import HypernovaOrchestrator, OrchestrationConfig
from .renderers import HypernovaAsciiRenderer, HypernovaJsonRenderer, HypernovaTextRenderer
from .saga import HypernovaSagaBuilder, SagaBeat
from .symphony import HypernovaSymphony, NovaInstrument, ScoreFragment

__all__ = [
    "AstroConduit",
    "ChronicleIndex",
    "ContinuumDomain",
    "EchoHypernode",
    "HyperCelestialMatrix",
    "HypernovaAsciiRenderer",
    "HypernovaBlueprint",
    "HypernovaJsonRenderer",
    "HypernovaOrchestrator",
    "HypernovaSagaBuilder",
    "HypernovaSymphony",
    "HyperpulseStream",
    "MythicStratum",
    "NovaInstrument",
    "OrchestrationConfig",
    "ResonantGlyph",
    "ResonantSignature",
    "SagaBeat",
    "ScoreFragment",
]
