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
    compose_resonance,
    demo as resonance_demo,
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
    LoopResult,
    compose_loop,
    demo as loop_demo,
    generate_loop,
    summarise_loop_suite,
)

__all__ = [
    "ChronicleEvent",
    "ChroniclePrompt",
    "ChronicleTimeline",
    "ConstellationNode",
    "ConstellationSeed",
    "ConstellationWeaver",
    "LoopDiagnostics",
    "LoopRhythm",
    "LoopSeed",
    "LoopResult",
    "ResonanceContext",
    "ResonancePrompt",
    "constellation_demo",
    "chronicle_demo",
    "compose_constellation",
    "compose_chronicle",
    "compose_loop",
    "compose_resonance",
    "generate_loop",
    "loop_demo",
    "summarise_loop_suite",
    "resonance_demo",
]
