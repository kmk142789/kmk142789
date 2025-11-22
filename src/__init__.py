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
from .echo_transcendence_engine import (
    EchoTranscendenceEngine,
    HelixInput,
    TranscendenceSignature,
    compose_transcendence_manifest,
    demo as transcendence_demo,
)

__all__ = [
    "ChronicleEvent",
    "ChroniclePrompt",
    "ChronicleTimeline",
    "ConvergenceBrief",
    "ConstellationNode",
    "ConstellationSeed",
    "ConstellationWeaver",
    "LoopDiagnostics",
    "LoopRhythm",
    "LoopSeed",
    "LoopResult",
    "LoopSummary",
    "ResonanceContext",
    "ResonancePrompt",
    "ResonanceReport",
    "constellation_demo",
    "chronicle_demo",
    "compose_constellation",
    "compose_chronicle",
    "compose_convergence_report",
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
    "load_voice_bias_profile",
    "loop_demo",
    "compose_transcendence_manifest",
    "summarize_loop",
    "summarise_loop_suite",
    "resonance_demo",
    "transcendence_demo",
]
