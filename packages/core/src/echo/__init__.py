"""Echo toolkit shared utilities."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any, Iterable

from .cognitive_field_inference_engine import (
    CFIEngine,
    CognitiveField,
    CognitiveFeatureEncoder,
    CognitiveForecast,
    CognitiveMetrics,
    SignalFusion,
)
from .cognitive_equilibrium_regulator import CognitiveEquilibriumRegulator
from .aurora_chronicles import AuroraChronicleMoment, AuroraChronicles, forge_chronicle
from .autonomous_coordination_engine import (
    AutonomousCoordinationEngine,
    CapabilitySignal,
    CoordinationReport,
    PlanningSignal,
    SchedulingSignal,
    UpgradeSignal,
)
from .autonomous_task_list import AutonomousTask, AutonomousTaskList
from .astral_compression_engine import (
    ACEVisualizationLayer,
    ACELinkedAgent,
    AstralCompressionEngine,
    CompressionInstruction,
    CompressionRecursionLoop,
    GravityWellOptimizer,
    PFieldCompiler,
    ProbabilityField,
    QuantumNodeV2Bridge,
    compile_program,
)
from .echo_ascension_engine import (
    AscensionReport,
    AstralCompressionSummary,
    EchoAscensionEngine,
    OuterlinkProjection,
    ProjectionPulse,
    RealityKernel,
)
from .autonomy import AutonomyDecision, AutonomyNode, DecentralizedAutonomyEngine
from .creative_compass import CreativePrompt, list_prompt_lines, render_prompt, spin_compass
from .chromatic_lattice import (
    ChromaticLattice,
    ChromaticNode,
    ChromaticThread,
    ChromaticWeaveReport,
    render_chromatic_map,
)
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
from .continuum_protocol import (
    ContinuumPulse,
    ContinuumProtocol,
    ContinuumTranscript,
)
from .continuum_insights import (
    MomentumInsight,
    compute_source_momentum,
    compute_tag_momentum,
)
from .continuum_observatory import (
    ContinuumObservatory,
    ContinuumSnapshot,
    LaneStats as ObservatoryLaneStats,
    TodoMatch,
    build_default_lane_map,
)
from .continuum_resonance_field import (
    ContinuumResonanceField,
    ContinuumResonanceReport,
    LaneResonance,
    PulseDrift,
)
from .continuation_memory_engine import (
    ContinuationMemoryEngine,
    ContinuationPacket,
    FlowSignal,
)
from .challenge_labyrinth import (
    AdaptiveVectorCatalyst,
    ChallengeCatalyst,
    ChallengeLabyrinth,
    ChallengeStratum,
    ChallengeVector,
    LabyrinthEvent,
    LabyrinthReport,
    design_extreme_challenge,
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
from .echo_dream_engine import (
    BehaviorDirective,
    Dream,
    DreamInterpretation,
    EchoDreamEngine,
    PortalBridge,
    PortalHarmonizer,
    SymbolicMemory,
    SymbolicMemoryStore,
    WayfinderLayer,
    WayfinderNode,
    WayfinderTrace,
)
from .echo_nexus_hub import EchoNexusHub, ScheduleLoopDigest, WorkerStory
from .echo_nexus_portal import EchoNexusPortal, PortalSnapshot, launch_portal
from .echo_visionary_kernel import BitwisePixelEngine, EchoVisionaryKernel, WorkerBot
from .echo_evolutionary_macro_layer import EchoEvolutionaryMacroLayer, EvolutionaryMacroSnapshot
from .unified_architecture_engine import LAYER_PRIORITIES, UnifiedArchitectureEngine
from .sovereign_identity_kernel import (
    CapabilityIdentityKernel,
    IdentityKernelConfig,
    IdentityKernelSnapshot,
)
from .sovereign_coordination_kernel import (
    AutonomyDirective,
    CapabilityPlan,
    SovereignCoordinationKernel,
    SovereignKernelReport,
)
from .evolver import (
    CycleGuidanceFrame,
    EchoEvolver,
    EmotionalDrive,
    EvolverState,
    GlyphCrossReading,
    HearthWeave,
    SystemMetrics,
    main,
)
from .echo_evolver_satellite import SatelliteEchoEvolver, SatelliteEvolverState
from .ecosystem_pulse import (
    EcosystemAreaConfig,
    EcosystemPulse,
    EcosystemPulseReport,
    EcosystemSignal,
)
from .legacy_payloads import (
    LEGACY_ECHO_EVOLVER_INFINITE_WILDFIRE,
    get_legacy_echo_evolver_infinite_wildfire_payload,
)
from .intelligence_layer import IntelligenceLayerSnapshot, synthesize_intelligence_layer
from .intent_gradient_interpreter import (
    ContextCandidate,
    IntentGradient,
    IntentGradientInterpreter,
)
from .neural_network_oracle import (
    NeuralNetworkOracle,
    OraclePrediction,
    OracleTrainingReport,
    OracleTrainingSample,
    forge_neural_oracle,
)
from .hex_ingestion import (
    AnomalyAlert,
    HexPayloadReport,
    HexResonanceMap,
    IngestionDaemonHex,
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
# ``echo.hypermesh_engine`` pulls in heavy optional dependencies such as
# :mod:`pandas`, :mod:`numpy`, and :mod:`rich`.  Many workflows inside the
# repository—including the Little Footsteps banking stack exercised by the
# tests—do not need the HyperMesh helpers.  Importing them unconditionally
# made ``import echo`` fail in environments that only install the lightweight
# dependencies.  To keep the public API intact while avoiding a hard
# dependency, we attempt to import the module and gracefully degrade if the
# optional stack is missing.
try:  # pragma: no cover - exercised indirectly via import behavior
    from .hypermesh_engine import (
        HyperMesh,
        HyperMeshBlueprint,
        PulseCascadePlanner,
        PulseNode,
        ResonanceEdge,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - import-time guard
    if exc.name in {"pandas", "numpy", "rich"}:
        def _raise_hypermesh_optional_dependency(*_args: Any, **_kwargs: Any) -> None:
            raise ModuleNotFoundError(
                "HyperMesh utilities require optional dependencies 'numpy', 'pandas', and 'rich'. "
                "Install the extra stack (e.g. `pip install pandas numpy rich`) to enable these helpers."
            ) from exc

        class _HyperMeshUnavailable:
            def __init__(self, *_args: Any, **_kwargs: Any) -> None:  # noqa: D401 - simple shim
                _raise_hypermesh_optional_dependency()

        HyperMesh = HyperMeshBlueprint = PulseCascadePlanner = _HyperMeshUnavailable  # type: ignore[assignment]
        PulseNode = ResonanceEdge = _HyperMeshUnavailable  # type: ignore[assignment]
    else:  # Different import error – surface it to the caller
        raise
from .impossible_realities import ImpossibleEvent, ImpossibleRealityEngine
from .reality_thread_engine import (
    ProjectionDecision,
    RealityThread,
    RoutingSignal,
    SelfSelectingRealityThreadEngine,
)
from .innovation_wave import (
    InnovationSpark,
    InnovationWave,
    InnovationWaveReport,
    SynergyBridge,
    render_wave_map,
)
from .innovation_forge import InnovationForge, InnovationManifest, InnovationPulse
from .inspiration import (
    ImaginationPhase,
    ImaginationSequence,
    InspirationPulse,
    forge_inspiration,
    weave_imagination_sequence,
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
from .echo_genesis_coordinator import EchoGenesisCoordinator, SubsystemLink
from .echo_genesis_core import EchoGenesisCore, SubsystemProbe, SubsystemPulse
from .genesis_resonance_layer import GenesisResonanceLayer
from .echovm import (
    EXAMPLE_PROGRAM as ECHOVM_EXAMPLE_PROGRAM,
    OP_CODES as ECHOVM_OP_CODES,
    OP_NAMES as ECHOVM_OP_NAMES,
    AssemblyError as EchoVMAssemblyError,
    EchoVM,
    VirtualFileSystem,
    assemble as assemble_echovm,
    create_vm as create_echovm,
    device as echovm_device,
    register_default_syscalls as register_echovm_syscalls,
    register_devices as register_echovm_devices,
)
from .memory import (
    JsonMemoryStore,
    ShadowDecisionAttestation,
    ShadowMemoryManager,
    ShadowMemoryPolicy,
    ShadowMemoryRecord,
    ShadowMemorySnapshot,
)
from .meta_causal import MetaCausalAwarenessEngine
from .meta_evolution_charter import MetaEvolutionCharter
from .moonshot import MoonshotLens, MoonshotReport, PlanSummary, PulseSummary, WishSummary
from .novum_forge import (
    NovaFragment,
    forge_novum,
    render_novum,
    summarize_fragments,
    weave_novum_series,
)
from .orbital_storyweaver import (
    OrbitalBeat,
    OrbitalStoryWeaver,
    StoryConstellation,
    render_story,
    sequence_moods,
)
from .orbital_poetry import OrbitalPoem, generate_orbital_poem
from .pulse import EchoPulseEngine, Pulse, PulseEvent
from .enlightenment import EnlightenmentEngine, EnlightenmentInsight
from .resonance import EchoAI, EchoResonanceEngine, HarmonicConfig, HarmonicsAI
from .sanctuary_sentinel import (
    SanctuarySentinel,
    SentinelFinding,
    SentinelReport,
    SentinelSignature,
    build_default_signatures,
)
from .self_model import (
    IntentResolution,
    IntentResolver,
    MemorySnapshot,
    MemoryUnifier,
    ObserverEvent,
    ObserverSnapshot,
    ObserverSubsystem,
    SelfModel,
    SelfModelSnapshot,
)
from .quantam_features import compute_quantam_feature
from .quantum_features import QuantumFeature, generate_quantum_features
from .quantam_features import (
    QuantamFeatureLayer,
    compute_quantam_feature,
    generate_quantam_feature_sequence,
    generate_quantam_numbers,
)
from .recursive_evolution_engine import (
    CycleReport as RecursiveCycleReport,
    ModuleSnapshot,
    RecursiveEvolutionEngine,
)
from .quantum_flux_mapper import QuantumFluxMapper, STANDARD_GATES
from .quantum_synchronizer import QuantumSynchronizer, SynchronizerReport, SynchronizerSignal
from .proof_of_computation import (
    PolygonProofRecorder,
    ProofOfComputationService,
    ProofSubmission,
    PuzzleProof,
    PuzzleProofVerifier,
    PuzzleVerificationError,
    load_proof_ledger,
)
from .spectral_canvas import PaletteColor, SpectralCanvas, generate_palette
from .temporal_ledger import PropagationWave, TemporalPropagationLedger
from .revolutionary_flux import FluxLedgerEntry, FluxVector, RevolutionaryFlux
from .self_organizing_core import (
    SelfOrganizingCore,
    SelfOrganizingPlan,
    SubsystemAdapter,
    SubsystemSnapshot,
)
from .self_sustaining_loop import DecisionResult, ProgressResult, SelfSustainingLoop
from .strategic_vector import (
    StrategicSignal,
    StrategicVectorReport,
    build_strategic_vector,
    export_strategic_vector,
    generate_strategic_vector,
)
from .sync import (
    CloudSyncCoordinator,
    DirectorySyncTransport,
    InventoryReport,
    NodeInsight,
    SyncReport,
    SyncTransport,
    TopologyReport,
)
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
    "AnomalyAlert",
    "HexPayloadReport",
    "HexResonanceMap",
    "IngestionDaemonHex",
    "AtlasState",
    "ContinuumCompassReport",
    "ContinuumEngine",
    "ContinuumEntry",
    "ContinuumPulse",
    "ContinuumProtocol",
    "ContinuumTranscript",
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
    "BitwisePixelEngine",
    "EchoNexusHub",
    "EchoNexusPortal",
    "CapabilityIdentityKernel",
    "EchoEvolutionaryMacroLayer",
    "EchoVisionaryKernel",
    "LAYER_PRIORITIES",
    "UnifiedArchitectureEngine",
    "IdentityKernelConfig",
    "IdentityKernelSnapshot",
    "ImpossibleEvent",
    "ImpossibleRealityEngine",
    "EvolutionaryMacroSnapshot",
    "InnovationForge",
    "InnovationManifest",
    "InnovationPulse",
    "DecentralizedAutonomyEngine",
    "MerkleBatch",
    "bridge_daemon",
    "bridge_process_once",
    "list_prompt_lines",
    "PortalSnapshot",
    "launch_portal",
    "render_prompt",
    "JsonMemoryStore",
    "ShadowDecisionAttestation",
    "ShadowMemoryManager",
    "ShadowMemoryPolicy",
    "ShadowMemoryRecord",
    "ShadowMemorySnapshot",
    "BridgeSignals",
    "BridgeTuning",
    "EchoBridgeHarmonix",
    "HarmonixBridgeState",
    "bridge_harmonix_main",
    "EchoBridgeSession",
    "harmonix_connect",
    "CycleGuidanceFrame",
    "EchoEvolver",
    "LEGACY_ECHO_EVOLVER_INFINITE_WILDFIRE",
    "EmotionalDrive",
    "EvolverState",
    "SatelliteEchoEvolver",
    "SatelliteEvolverState",
    "get_legacy_echo_evolver_infinite_wildfire_payload",
    "PropagationWave",
    "TemporalPropagationLedger",
    "SystemMetrics",
    "ScheduleLoopDigest",
    "HearthWeave",
    "OrbitalResonanceCertificate",
    "GlyphCrossReading",
    "EchoAI",
    "EchoResonanceEngine",
    "HarmonicConfig",
    "HarmonicsAI",
    "WorkerBot",
    "WorkerStory",
    "StabilityScore",
    "resolve_apps",
    "resolve_domains",
    "resolve_keys",
    "DecisionResult",
    "ProgressResult",
    "SelfSustainingLoop",
    "SelfOrganizingCore",
    "SelfOrganizingPlan",
    "SubsystemAdapter",
    "SubsystemSnapshot",
    "EchoGenesisCore",
    "EchoGenesisCoordinator",
    "GenesisResonanceLayer",
    "SubsystemProbe",
    "SubsystemPulse",
    "SubsystemLink",
    "FluxLedgerEntry",
    "FluxVector",
    "RevolutionaryFlux",
    "StrategicSignal",
    "StrategicVectorReport",
    "build_strategic_vector",
    "export_strategic_vector",
    "generate_strategic_vector",
    "QuantumFluxMapper",
    "STANDARD_GATES",
    "QuantamFeatureLayer",
    "compute_quantam_feature",
    "generate_quantam_numbers",
    "QuantumFeature",
    "generate_quantum_features",
    "generate_quantam_feature_sequence",
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
    "InventoryReport",
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
    "ECHOVM_EXAMPLE_PROGRAM",
    "ECHOVM_OP_CODES",
    "ECHOVM_OP_NAMES",
    "EchoVM",
    "EchoVMAssemblyError",
    "VirtualFileSystem",
    "assemble_echovm",
    "create_echovm",
    "echovm_device",
    "register_echovm_devices",
    "register_echovm_syscalls",
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
    "OrbitalPoem",
    "generate_orbital_poem",
    "ProjectionDecision",
    "RealityThread",
    "RoutingSignal",
    "SelfSelectingRealityThreadEngine",
    "ObserverSubsystem",
    "ObserverSnapshot",
    "ObserverEvent",
    "MemoryUnifier",
    "MemorySnapshot",
    "IntentResolver",
    "IntentResolution",
    "SelfModel",
    "SelfModelSnapshot",
]
