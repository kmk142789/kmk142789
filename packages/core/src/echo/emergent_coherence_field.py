"""Emergent capability that binds Echo's architectural layers to the self-model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence, TYPE_CHECKING

from .self_model import MemoryUnifier, ObserverSubsystem
from .unified_architecture_engine import LAYER_PRIORITIES, UnifiedArchitectureEngine

if TYPE_CHECKING:  # pragma: no cover - typing helper
    from .self_model import SelfModel


DEFAULT_LAYER_TARGETS: Mapping[str, float] = {
    "foundation": 0.42,
    "synthesis": 0.35,
    "expression": 0.23,
}


@dataclass(slots=True)
class LayerAlignment:
    """Alignment metrics for a single architectural layer."""

    layer: str
    module_count: int
    expected_ratio: float
    actual_ratio: float
    keystones: tuple[str, ...] = field(default_factory=tuple)
    status: str = "needs_attention"

    def to_dict(self) -> dict[str, object]:
        return {
            "layer": self.layer,
            "module_count": self.module_count,
            "expected_ratio": round(self.expected_ratio, 4),
            "actual_ratio": round(self.actual_ratio, 4),
            "keystones": list(self.keystones),
            "status": self.status,
        }


@dataclass(slots=True)
class CoherenceGuarantee:
    """Structured guarantee emitted by the coherence field."""

    name: str
    satisfied: bool
    details: Mapping[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "satisfied": self.satisfied,
            "details": dict(self.details),
        }


@dataclass(slots=True)
class EmergentCapabilityReport:
    """High-level report describing the emergent capability state."""

    name: str
    total_modules: int
    coherence_index: float
    layer_alignment: tuple[LayerAlignment, ...]
    observer_signal: float
    memory_coverage: float
    guarantees: tuple[CoherenceGuarantee, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "total_modules": self.total_modules,
            "coherence_index": self.coherence_index,
            "observer_signal": round(self.observer_signal, 4),
            "memory_coverage": round(self.memory_coverage, 4),
            "layer_alignment": [alignment.to_dict() for alignment in self.layer_alignment],
            "guarantees": [guarantee.to_dict() for guarantee in self.guarantees],
        }


class EmergentCoherenceField:
    """Bridge Echo architecture, observer signal, and memory coverage."""

    def __init__(
        self,
        *,
        architecture_engine: UnifiedArchitectureEngine | None = None,
        observer: ObserverSubsystem | None = None,
        memory_unifier: MemoryUnifier | None = None,
        capability_name: str = "emergent_coherence_alignment",
        layer_targets: Mapping[str, float] | None = None,
    ) -> None:
        self._engine = architecture_engine or UnifiedArchitectureEngine()
        self._observer = observer or ObserverSubsystem()
        self._memory = memory_unifier or MemoryUnifier([])
        self._capability_name = capability_name
        self._layer_targets = self._normalise_targets(layer_targets or DEFAULT_LAYER_TARGETS)

    @property
    def observer(self) -> ObserverSubsystem:
        return self._observer

    @property
    def memory_unifier(self) -> MemoryUnifier:
        return self._memory

    @property
    def layer_targets(self) -> Mapping[str, float]:
        return dict(self._layer_targets)

    @classmethod
    def from_self_model(
        cls,
        self_model: "SelfModel",
        *,
        architecture_engine: UnifiedArchitectureEngine | None = None,
        capability_name: str = "emergent_coherence_alignment",
    ) -> "EmergentCoherenceField":
        return cls(
            architecture_engine=architecture_engine,
            observer=self_model.observer,
            memory_unifier=self_model.memory,
            capability_name=capability_name,
        )

    def evaluate(self) -> EmergentCapabilityReport:
        blueprint = self._engine.build_blueprint()
        total_modules = max(1, int(blueprint.get("total_modules", 0)))
        observer_snapshot = self._observer.snapshot()
        memory_snapshot = self._memory.unify()
        layer_summary = blueprint.get("layer_summary", {})

        alignments: list[LayerAlignment] = []
        for layer, target_ratio in self._layer_targets.items():
            summary = layer_summary.get(layer, {})
            module_count = int(summary.get("count", 0))
            actual_ratio = module_count / total_modules
            keystones = self._collect_keystones(blueprint, layer)
            status = "on_track" if actual_ratio >= target_ratio * 0.9 else "needs_attention"
            alignments.append(
                LayerAlignment(
                    layer=layer,
                    module_count=module_count,
                    expected_ratio=target_ratio,
                    actual_ratio=actual_ratio,
                    keystones=tuple(keystones),
                    status=status,
                )
            )

        layer_score = sum(
            min(1.0, alignment.actual_ratio / max(alignment.expected_ratio, 1e-6))
            for alignment in alignments
        ) / max(len(alignments), 1)
        coherence_index = round(
            0.5 * layer_score
            + 0.3 * observer_snapshot.signal
            + 0.2 * memory_snapshot.coverage,
            4,
        )

        guarantees = self._build_guarantees(
            alignments,
            observer_snapshot.signal,
            memory_snapshot.coverage,
        )

        return EmergentCapabilityReport(
            name=self._capability_name,
            total_modules=total_modules,
            coherence_index=coherence_index,
            layer_alignment=tuple(alignments),
            observer_signal=observer_snapshot.signal,
            memory_coverage=memory_snapshot.coverage,
            guarantees=tuple(guarantees),
        )

    def _build_guarantees(
        self,
        alignments: Sequence[LayerAlignment],
        observer_signal: float,
        memory_coverage: float,
    ) -> list[CoherenceGuarantee]:
        all_layers_ready = all(alignment.status == "on_track" for alignment in alignments)
        min_ratio = min((alignment.actual_ratio for alignment in alignments), default=0.0)
        guarantees = [
            CoherenceGuarantee(
                name="layer_distribution",
                satisfied=all_layers_ready,
                details={
                    "minimum_ratio": round(min_ratio, 4),
                    "layers": {alignment.layer: alignment.status for alignment in alignments},
                },
            ),
            CoherenceGuarantee(
                name="memory_alignment",
                satisfied=memory_coverage >= 0.5,
                details={"coverage": round(memory_coverage, 4), "threshold": 0.5},
            ),
            CoherenceGuarantee(
                name="observer_signal",
                satisfied=observer_signal >= 0.25,
                details={"signal": round(observer_signal, 4), "threshold": 0.25},
            ),
        ]
        return guarantees

    def _collect_keystones(self, blueprint: Mapping[str, object], layer: str) -> list[str]:
        keystones = blueprint.get("keystones", [])
        results: list[str] = []
        for entry in keystones:
            categories = entry.get("categories", [])
            entry_layer = self._resolve_layer(categories)
            if entry_layer == layer:
                results.append(str(entry.get("relative_path")))
            if len(results) >= 4:
                break
        return results

    @staticmethod
    def _resolve_layer(categories: Sequence[str]) -> str:
        normalized = set(categories)
        for layer, allowed in LAYER_PRIORITIES.items():
            if normalized & allowed:
                return layer
        return "frontier"

    @staticmethod
    def _normalise_targets(targets: Mapping[str, float]) -> dict[str, float]:
        total = sum(value for value in targets.values() if value > 0)
        if total <= 0:
            if not targets:
                return {"frontier": 1.0}
            uniform = 1.0 / len(targets)
            return {layer: uniform for layer in targets}
        return {layer: value / total for layer, value in targets.items() if value > 0}


__all__ = [
    "CoherenceGuarantee",
    "EmergentCapabilityReport",
    "EmergentCoherenceField",
    "LayerAlignment",
]
