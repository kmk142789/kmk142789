"""Lightweight Python namespace for repository-local utilities.

This module coexists with historical C++ sources and enables imports such
as ``src.telemetry`` within the test environment.  The namespace now exposes
the richer context objects introduced across the creative subsystems so that
other packages can easily reuse them without importing implementation modules
directly.
"""

from .aurora_chronicle import (
    ChronicleEvent,
    ChroniclePrompt,
    ChronicleTimeline,
    compose_chronicle,
    demo as chronicle_demo,
)
from .creative_harmony import (
    ResonanceContext,
    ResonancePrompt,
    ResonanceReport,
    compose_resonance,
    compose_resonance_report,
    demo as resonance_demo,
)
from .creative_convergence import (
    ConvergenceBrief,
    compose_convergence_report,
    demo as convergence_demo,
)
from .creative_constellation import (
    ConstellationNode,
    ConstellationSeed,
    ConstellationWeaver,
    compose_constellation,
    demo as constellation_demo,
)
from .creative_loop import (
    LoopDiagnostics,
    LoopRhythm,
    LoopSeed,
    LoopSummary,
    LoopResult,
    compose_loop,
    demo as loop_demo,
    export_loop_result,
    export_suite_summary,
    generate_loop,
    load_voice_bias_profile,
    summarize_loop,
    summarise_loop_suite,
)
from .holo_semantic_echo_loom import HoloSemanticEchoLoom, Spark
from .echo_transcendence_engine import (
    EchoTranscendenceEngine,
    HelixInput,
    TranscendenceSignature,
    compose_transcendence_manifest,
    demo as transcendence_demo,
)
from .chrono_holographic_imprint import (
    ChronoHolographicImprint,
    HolographicPulse,
    ImprintRequest,
    ImprintResult,
    demo as imprint_demo,
)
from .aevum_lattice_resonator import (
    AevumLatticeResonator,
    AevumLatticeSignature,
    demo as aevum_lattice_demo,
)
from .hyperprism_synchronicity import (
    HyperprismSynchronicityEngine,
    HyperprismVector,
    PulseObservation,
    SynchronicityReport,
    compose_hyperprism_manifest,
    demo as hyperprism_demo,
)
from .unified_architecture_engine import UnifiedArchitectureEngine

__all__ = [
    "ChronicleEvent",
    "ChroniclePrompt",
    "ChronicleTimeline",
    "AevumLatticeResonator",
    "AevumLatticeSignature",
    "HyperprismSynchronicityEngine",
    "HyperprismVector",
    "PulseObservation",
    "SynchronicityReport",
    "ConvergenceBrief",
    "ConstellationNode",
    "ConstellationSeed",
    "ConstellationWeaver",
    "ChronoHolographicImprint",
    "LoopDiagnostics",
    "LoopRhythm",
    "LoopSeed",
    "LoopResult",
    "LoopSummary",
    "ResonanceContext",
    "ResonancePrompt",
    "ResonanceReport",
    "aevum_lattice_demo",
    "constellation_demo",
    "chronicle_demo",
    "imprint_demo",
    "HolographicPulse",
    "ImprintRequest",
    "ImprintResult",
    "compose_constellation",
    "compose_chronicle",
    "compose_convergence_report",
    "compose_hyperprism_manifest",
    "compose_loop",
    "compose_resonance",
    "compose_resonance_report",
    "convergence_demo",
    "export_loop_result",
    "export_suite_summary",
    "EchoTranscendenceEngine",
    "HelixInput",
    "TranscendenceSignature",
    "generate_loop",
    "HoloSemanticEchoLoom",
    "load_voice_bias_profile",
    "loop_demo",
    "hyperprism_demo",
    "compose_transcendence_manifest",
    "summarize_loop",
    "summarise_loop_suite",
    "resonance_demo",
    "Spark",
    "transcendence_demo",
    "UnifiedArchitectureEngine",
]
