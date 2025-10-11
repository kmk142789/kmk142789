"""Echo toolkit shared utilities."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from .bridge_emitter import (
    BridgeConfig,
    BridgeEmitter,
    BridgeState,
    MerkleBatch,
    daemon as bridge_daemon,
    process_once as bridge_process_once,
)
from .evolver import EchoEvolver, EmotionalDrive, EvolverState, SystemMetrics, main
from .pulse_ledger import (
    DEFAULT_ANCHOR,
    DEFAULT_LEDGER_PATH,
    PulseEntry,
    PulseLedger,
    PulseLedgerState,
    PulseSnapshot,
)
from .resonance import EchoAI, EchoResonanceEngine, HarmonicConfig, HarmonicsAI
from .thoughtlog import ThoughtLogger, thought_trace

if TYPE_CHECKING:  # pragma: no cover - import-time convenience for type checkers
    from .idea_processor import IdeaAnalysis, IdeaProcessor, IdeaResult, process_idea

_LAZY_MODULES = {
    "IdeaAnalysis": "idea_processor",
    "IdeaProcessor": "idea_processor",
    "IdeaResult": "idea_processor",
    "process_idea": "idea_processor",
}


def __getattr__(name: str) -> Any:  # pragma: no cover - thin forwarding shim
    if name in _LAZY_MODULES:
        module = import_module(f".{_LAZY_MODULES[name]}", __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BridgeConfig",
    "BridgeEmitter",
    "BridgeState",
    "MerkleBatch",
    "bridge_daemon",
    "bridge_process_once",
    "EchoEvolver",
    "EmotionalDrive",
    "EvolverState",
    "SystemMetrics",
    "PulseEntry",
    "PulseLedger",
    "PulseLedgerState",
    "PulseSnapshot",
    "DEFAULT_ANCHOR",
    "DEFAULT_LEDGER_PATH",
    "EchoAI",
    "EchoResonanceEngine",
    "HarmonicConfig",
    "HarmonicsAI",
    "ThoughtLogger",
    "thought_trace",
    "main",
    "IdeaAnalysis",
    "IdeaProcessor",
    "IdeaResult",
    "process_idea",
]
