"""Macro-layer extension that fuses sovereign identity telemetry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .echo_macro_layer import EchoMacroLayer, MacroLayerSnapshot
from .identity_layer import SovereignIdentityLayer


@dataclass(slots=True)
class EvolutionaryMacroSnapshot:
    """Composite snapshot emitted by :class:`EchoEvolutionaryMacroLayer`."""

    macro: MacroLayerSnapshot
    sovereign_identity: Mapping[str, Any]


class EchoEvolutionaryMacroLayer:
    """Wraps :class:`EchoMacroLayer` with sovereign identity state."""

    def __init__(self, macro_layer: EchoMacroLayer, identity_layer: SovereignIdentityLayer) -> None:
        self._macro = macro_layer
        self._identity = identity_layer

    def evolve(
        self,
        *,
        proof_claim: Any | None = None,
        circuit: str | None = None,
        backend: str | None = None,
    ) -> EvolutionaryMacroSnapshot:
        """Run a macro cycle and stitch in sovereign identity telemetry."""

        macro_snapshot = self._macro.orchestrate(
            proof_claim=proof_claim,
            circuit=circuit,
            backend=backend,
        )
        identity_snapshot = self._identity.snapshot()
        return EvolutionaryMacroSnapshot(macro=macro_snapshot, sovereign_identity=identity_snapshot)


__all__ = ["EchoEvolutionaryMacroLayer", "EvolutionaryMacroSnapshot"]
