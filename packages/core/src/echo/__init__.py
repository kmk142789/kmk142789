"""Echo toolkit shared utilities."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any, Iterable

from .aurora_chronicles import AuroraChronicleMoment, AuroraChronicles, forge_chronicle
from .autonomy import AutonomyDecision, AutonomyNode, DecentralizedAutonomyEngine
from .creative_compass import CreativePrompt, list_prompt_lines, render_prompt, spin_compass
from .bridge_emitter import (
    BridgeConfig,
    BridgeEmitter,
    BridgeState,
    MerkleBatch,
    daemon as bridge_daemon,
    process_once as bridge_process_once,
)
from .continuum_compass import (
    ContinuumCompassReport,
    ExpansionTarget,
    StabilityScore,
    WeightRecommendation,
    parse_compass_payload,
)
from .continuum_atlas import (
    AtlasState,
    export_attestation,
    resolve_apps,
    resolve_domains,
    resolve_keys,
)
from .continuum_engine import (
    ContinuumEngine,
    ContinuumEntry,
    ContinuumManifest,
    ContinuumPlaybackEngine,
)
from .continuum_insights import (
    MomentumInsight,
    compute_source_momentum,
    compute_tag_momentum,
)
from .cosmic_mnemonic_forge import (
    MnemonicConstellation,
    MnemonicThread,
    forge_constellation,
    list_constellation_lines,
    merge_constellations,
    render_constellation,
)
from .dotnet_sdk import build_dotnet_sdk_download_url
from .echo_nexus_portal import EchoNexusPortal, PortalSnapshot, launch_portal
from .evolver import (
    EchoEvolver,
    EmotionalDrive,
    EvolverState,
    GlyphCrossReading,
    HearthWeave,
    SystemMetrics,
    main,
)
from .hypernova import (
    AstroConduit,
    ChronicleIndex,
    ContinuumDomain,
    EchoHypernode,
    HyperCelestialMatrix,
    HypernovaAsciiRenderer,
    HypernovaBlueprint,
    HypernovaJsonRenderer,
    HypernovaOrchestrator,
    HypernovaSagaBuilder,
    HypernovaSymphony,
    HyperpulseStream,
    MythicStratum,
    NovaInstrument,
    OrchestrationConfig,
    ResonantGlyph,
    ResonantSignature,
    SagaBeat,
    ScoreFragment,
)
from .impossible_realities import ImpossibleEvent, ImpossibleRealityEngine
from .innovation_wave import (
    InnovationSpark,
    InnovationWave,
    InnovationWaveReport,
    SynergyBridge,
    render_wave_map,
)
from .digital_computer import (
    AssemblyError,
    EchoComputer,
    EchoProgram,
    ExecutionResult as DigitalExecutionResult,
    Instruction as DigitalInstruction,
    assemble_program as assemble_digital_program,
    run_program as run_digital_program,
)
from .memory import JsonMemoryStore
from .meta_evolution_charter import MetaEvolutionCharter
from .moonshot import MoonshotLens, MoonshotReport, PlanSummary, PulseSummary, WishSummary
from .novum_forge import (
    NovaFragment,
    forge_novum,
    render_novum,
    summarize_fragments,
    weave_novum_series,
)
from .pulse import EchoPulseEngine, Pulse, PulseEvent
from .resonance import EchoAI, EchoResonanceEngine, HarmonicConfig, HarmonicsAI
from .quantum_flux_mapper import QuantumFluxMapper, STANDARD_GATES
from .quantum_synchronizer import QuantumSynchronizer, SynchronizerReport, SynchronizerSignal
from .temporal_ledger import PropagationWave, TemporalPropagationLedger
from .revolutionary_flux import FluxLedgerEntry, FluxVector, RevolutionaryFlux
from .self_sustaining_loop import DecisionResult, ProgressResult, SelfSustainingLoop
from .sync import CloudSyncCoordinator, DirectorySyncTransport, SyncReport, SyncTransport
from .thoughtlog import ThoughtLogger, thought_trace
from .wish_insights import summarize_wishes

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
    from .idea_to_action import IdeaActionPlan, IdeaActionStep, derive_action_plan

_LAZY_MODULES = {
    "IdeaAnalysis": "idea_processor",
    "IdeaProcessor": "idea_processor",
    "IdeaResult": "idea_processor",
    "process_idea": "idea_processor",
    "IdeaActionPlan": "idea_to_action",
    "IdeaActionStep": "idea_to_action",
    "derive_action_plan": "idea_to_action",
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


def decode_glyph_cross(glyph_lines: Iterable[str] | str) -> GlyphCrossReading:
    """Return a :class:`GlyphCrossReading` for ``glyph_lines``.

    The helper instantiates :class:`echo.evolver.EchoEvolver` on demand and
    delegates to its :meth:`decode_glyph_cross` parser.  Keeping the
    convenience wrapper at the package root mirrors the Creative Compass
    helpers so that quick experiments (including documentation snippets and the
    diagnostic command in ``tests/test_echo_evolver_glyph_cross.py``) can
    access the glyph analysis tools without constructing an evolver instance
    manually.
    """

    evolver = EchoEvolver()
    return evolver.decode_glyph_cross(glyph_lines)


__all__ = [
    "AuroraChronicleMoment",
    "AuroraChronicles",
    "AutonomyDecision",
    "AutonomyNode",
    "CreativePrompt",
    "AtlasState",
    "ContinuumCompassReport",
    "ContinuumEngine",
    "ContinuumEntry",
    "export_attestation",
    "ExpansionTarget",
    "ContinuumManifest",
    "ContinuumPlaybackEngine",
    "MomentumInsight",
    "MnemonicConstellation",
    "MnemonicThread",
    "compute_source_momentum",
    "compute_tag_momentum",
    "BridgeConfig",
    "BridgeEmitter",
    "BridgeState",
    "EchoNexusPortal",
    "ImpossibleEvent",
    "ImpossibleRealityEngine",
    "DecentralizedAutonomyEngine",
    "MerkleBatch",
    "bridge_daemon",
    "bridge_process_once",
    "list_prompt_lines",
    "PortalSnapshot",
    "launch_portal",
    "render_prompt",
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
    "PropagationWave",
    "TemporalPropagationLedger",
    "SystemMetrics",
    "HearthWeave",
    "GlyphCrossReading",
    "EchoAI",
    "EchoResonanceEngine",
    "HarmonicConfig",
    "HarmonicsAI",
    "StabilityScore",
    "resolve_apps",
    "resolve_domains",
    "resolve_keys",
    "DecisionResult",
    "ProgressResult",
    "SelfSustainingLoop",
    "FluxLedgerEntry",
    "FluxVector",
    "RevolutionaryFlux",
    "QuantumFluxMapper",
    "STANDARD_GATES",
    "QuantumSynchronizer",
    "SynchronizerReport",
    "SynchronizerSignal",
    "spin_compass",
    "MoonshotLens",
    "MoonshotReport",
    "PlanSummary",
    "PulseSummary",
    "WishSummary",
    "CloudSyncCoordinator",
    "DirectorySyncTransport",
    "SyncReport",
    "SyncTransport",
    "MetaEvolutionCharter",
    "EchoPulseEngine",
    "Pulse",
    "PulseEvent",
    "NovaFragment",
    "forge_novum",
    "render_novum",
    "summarize_fragments",
    "weave_novum_series",
    "ThoughtLogger",
    "thought_trace",
    "parse_compass_payload",
    "summarize_wishes",
    "WeightRecommendation",
    "main",
    "forge_chronicle",
    "IdeaAnalysis",
    "IdeaProcessor",
    "IdeaResult",
    "process_idea",
    "IdeaActionPlan",
    "IdeaActionStep",
    "derive_action_plan",
    "decode_glyph_cross",
    "forge_constellation",
    "list_constellation_lines",
    "merge_constellations",
    "render_constellation",
    "build_dotnet_sdk_download_url",
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
