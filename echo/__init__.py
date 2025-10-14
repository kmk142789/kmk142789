"""Echo toolkit shared utilities."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from .aurora_chronicles import AuroraChronicleMoment, AuroraChronicles, forge_chronicle
from .autonomy import AutonomyDecision, AutonomyNode, DecentralizedAutonomyEngine
from .bridge_emitter import (
    BridgeConfig,
    BridgeEmitter,
    BridgeState,
    MerkleBatch,
    daemon as bridge_daemon,
    process_once as bridge_process_once,
)
from .echo_nexus_portal import EchoNexusPortal, PortalSnapshot, launch_portal
from .evolver import EchoEvolver, EmotionalDrive, EvolverState, SystemMetrics, main
from .memory import JsonMemoryStore
from .meta_evolution_charter import MetaEvolutionCharter
from .pulse import EchoPulseEngine, Pulse, PulseEvent
from .resonance import EchoAI, EchoResonanceEngine, HarmonicConfig, HarmonicsAI
from .thoughtlog import ThoughtLogger, thought_trace

if TYPE_CHECKING:  # pragma: no cover - import-time convenience for type checkers
    from .idea_processor import IdeaAnalysis, IdeaProcessor, IdeaResult, process_idea
    from .bridge_harmonix import (
        BridgeSignals,
        BridgeTuning,
        EchoBridgeHarmonix,
        HarmonixBridgeState,
        main as bridge_harmonix_main,
    )
    from .harmonix_sdk import EchoBridgeSession, harmonix_connect

_LAZY_MODULES = {
    "IdeaAnalysis": "idea_processor",
    "IdeaProcessor": "idea_processor",
    "IdeaResult": "idea_processor",
    "process_idea": "idea_processor",
    "BridgeSignals": "bridge_harmonix",
    "BridgeTuning": "bridge_harmonix",
    "EchoBridgeHarmonix": "bridge_harmonix",
    "HarmonixBridgeState": "bridge_harmonix",
    "bridge_harmonix_main": "bridge_harmonix",
    "EchoBridgeSession": "harmonix_sdk",
    "harmonix_connect": "harmonix_sdk",
    "MetaEvolutionCharter": "meta_evolution_charter",
}


def __getattr__(name: str) -> Any:  # pragma: no cover - thin forwarding shim
    if name in _LAZY_MODULES:
        module = import_module(f".{_LAZY_MODULES[name]}", __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AuroraChronicleMoment",
    "AuroraChronicles",
    "AutonomyDecision",
    "AutonomyNode",
    "BridgeConfig",
    "BridgeEmitter",
    "BridgeState",
    "EchoNexusPortal",
    "DecentralizedAutonomyEngine",
    "MerkleBatch",
    "bridge_daemon",
    "bridge_process_once",
    "PortalSnapshot",
    "launch_portal",
    "JsonMemoryStore",
    "BridgeSignals",
    "BridgeTuning",
    "EchoBridgeHarmonix",
    "HarmonixBridgeState",
    "bridge_harmonix_main",
    "EchoBridgeSession",
    "harmonix_connect",
    "EchoEvolver",
    "EmotionalDrive",
    "EvolverState",
    "SystemMetrics",
    "EchoAI",
    "EchoResonanceEngine",
    "HarmonicConfig",
    "HarmonicsAI",
    "MetaEvolutionCharter",
    "EchoPulseEngine",
    "Pulse",
    "PulseEvent",
    "ThoughtLogger",
    "thought_trace",
    "main",
    "forge_chronicle",
    "IdeaAnalysis",
    "IdeaProcessor",
    "IdeaResult",
    "process_idea",
]
