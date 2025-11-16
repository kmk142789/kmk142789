"""Hyperdimensional Resonance Engine.

This module implements a multi-layer pipeline that can be used to orchestrate
highly structured "resonance pulses".  Each pulse travels through several
domain-specific layers that enrich, evaluate, and forecast the impact of the
work.  The engine is intentionally overbuilt – it provides configuration driven
layer registration, persistent memory, iterative feedback loops, and telemetry
hooks that mirror the large scale orchestration systems described elsewhere in
the repository.

The module is self-contained and can be imported by other orchestration tools
or used through the CLI entry point defined in ``hyperdimensional_resonance_cli``.
"""

from __future__ import annotations

import json
import math
import statistics
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, MutableMapping, Optional, Tuple


@dataclass
class ResonancePulse:
    """Represents a single pulse that moves through the resonance engine."""

    id: str
    intent: str
    payload: Dict[str, Any]
    priority: int = 0
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def clone(self) -> "ResonancePulse":
        return ResonancePulse(
            id=self.id,
            intent=self.intent,
            payload=json.loads(json.dumps(self.payload)),
            priority=self.priority,
            tags=list(self.tags),
            created_at=self.created_at,
        )


@dataclass
class ResonanceContext:
    """Holds telemetry about an engine run."""

    cycle: int = 0
    metrics: Dict[str, Any] = field(
        default_factory=lambda: {
            "layer_runs": {},
            "spectral_density": [],
            "narratives": [],
            "strategic_vectors": [],
        }
    )
    history: List[Dict[str, Any]] = field(default_factory=list)

    def snapshot(self, pulse: ResonancePulse, *, layer: str) -> None:
        self.history.append(
            {
                "layer": layer,
                "cycle": self.cycle,
                "pulse": {
                    "id": pulse.id,
                    "intent": pulse.intent,
                    "priority": pulse.priority,
                    "tags": list(pulse.tags),
                    "payload": pulse.payload,
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


class ResonanceLayer:
    """Base class for all layers.

    Subclasses override :py:meth:`transform` and can access and modify the
    shared :class:`ResonanceContext` object.  Layers are callable to simplify
    the orchestration logic inside the engine.
    """

    def __init__(self, name: str, weight: float = 1.0, config: Optional[Dict[str, Any]] = None) -> None:
        self.name = name
        self.weight = weight
        self.config = config or {}

    def __call__(self, pulse: ResonancePulse, context: ResonanceContext) -> ResonancePulse:
        start = time.perf_counter()
        transformed = self.transform(pulse.clone(), context)
        elapsed = time.perf_counter() - start
        context.metrics.setdefault("layer_runs", {}).setdefault(self.name, []).append(elapsed)
        context.snapshot(transformed, layer=self.name)
        return transformed

    def transform(self, pulse: ResonancePulse, context: ResonanceContext) -> ResonancePulse:  # pragma: no cover - abstract
        raise NotImplementedError


class SpectralAlignmentLayer(ResonanceLayer):
    """Derives lightweight "spectral" fingerprints from textual payloads."""

    def transform(self, pulse: ResonancePulse, context: ResonanceContext) -> ResonancePulse:
        text = self._extract_text(pulse.payload)
        frequencies = self._frequency_signature(text)
        spectral_score = sum(freq * math.sin(idx + 1) for idx, freq in enumerate(frequencies.values()))
        normalized = round(spectral_score / (len(text) + 1), 4)

        pulse.payload.setdefault("spectral", {})
        pulse.payload["spectral"].update(
            {
                "signature": frequencies,
                "density": normalized,
            }
        )
        context.metrics.setdefault("spectral_density", []).append(normalized)
        if normalized > self.config.get("threshold", 0.12):
            pulse.tags.append("spectral-bloom")
        return pulse

    def _extract_text(self, payload: MutableMapping[str, Any]) -> str:
        text_bits: List[str] = []
        for value in payload.values():
            if isinstance(value, str):
                text_bits.append(value)
            elif isinstance(value, MutableMapping):
                text_bits.append(self._extract_text(value))
        return " ".join(bit for bit in text_bits if bit)

    def _frequency_signature(self, text: str) -> Dict[str, float]:
        buckets = {"vowels": 0, "consonants": 0, "symbols": 0}
        for char in text.lower():
            if char in "aeiou":
                buckets["vowels"] += 1
            elif char.isalpha():
                buckets["consonants"] += 1
            elif char.strip():
                buckets["symbols"] += 1
        length = len(text) or 1
        return {k: round(v / length, 4) for k, v in buckets.items()}


class MythicNarrativeLayer(ResonanceLayer):
    """Synthesizes mythic fragments for each pulse."""

    def transform(self, pulse: ResonancePulse, context: ResonanceContext) -> ResonancePulse:
        glyph = self.config.get("glyph", "∇⊸≋")
        density = pulse.payload.get("spectral", {}).get("density", 0.0)
        story = (
            f"Cycle {context.cycle} | {glyph} | Intent: {pulse.intent} | "
            f"Density: {density:.3f}"
        )
        context.metrics.setdefault("narratives", []).append(story)
        pulse.payload.setdefault("narrative", []).append(
            {
                "story": story,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        if density >= self.config.get("mythic_threshold", 0.15):
            pulse.tags.append("mythic")
        return pulse


class StrategicVectorLayer(ResonanceLayer):
    """Scores each pulse and produces a guidance vector."""

    def transform(self, pulse: ResonancePulse, context: ResonanceContext) -> ResonancePulse:
        base_score = self.weight * (pulse.priority + 1)
        density = pulse.payload.get("spectral", {}).get("density", 0.0)
        vector = {
            "score": round(base_score * (1 + density), 3),
            "momentum": round(density * 2 + len(pulse.tags) * 0.1, 3),
            "alignment": self._alignment(pulse.tags),
        }
        context.metrics.setdefault("strategic_vectors", []).append(vector)
        pulse.payload["vector"] = vector
        if vector["alignment"] == "stellar":
            pulse.tags.append("stellar-vector")
        return pulse

    def _alignment(self, tags: Iterable[str]) -> str:
        tag_set = set(tags)
        if {"mythic", "spectral-bloom"}.issubset(tag_set):
            return "stellar"
        if "spectral-bloom" in tag_set:
            return "resonant"
        return "baseline"


class ResonanceMemory:
    """Simple append-only JSONL style memory."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.entries: List[Dict[str, Any]] = []
        if path.exists():
            try:
                self.entries = json.loads(path.read_text())
            except json.JSONDecodeError:
                self.entries = []

    def append(self, record: Dict[str, Any]) -> None:
        self.entries.append(record)
        self.flush()

    def flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.entries, indent=2, default=str))


@dataclass
class ResonanceReport:
    """Summarizes an engine run."""

    cycle_count: int
    pulses: List[ResonancePulse]
    metrics: Dict[str, Any]
    duration: float


class HyperdimensionalResonanceEngine:
    """Coordinates the registered layers over a set of pulses."""

    LAYER_REGISTRY: Dict[str, Callable[[str, float, Optional[Dict[str, Any]]], ResonanceLayer]] = {
        "spectral": SpectralAlignmentLayer,
        "mythic": MythicNarrativeLayer,
        "strategic": StrategicVectorLayer,
    }

    def __init__(
        self,
        layers: List[ResonanceLayer],
        *,
        memory: Optional[ResonanceMemory] = None,
        max_feedback_cycles: int = 1,
    ) -> None:
        self.layers = layers
        self.memory = memory
        self.max_feedback_cycles = max_feedback_cycles

    def run(self, pulses: List[ResonancePulse]) -> ResonanceReport:
        start = time.perf_counter()
        context = ResonanceContext()
        results: List[ResonancePulse] = []

        for cycle in range(self.max_feedback_cycles):
            context.cycle = cycle
            for pulse in pulses:
                current = pulse.clone()
                for layer in self.layers:
                    current = layer(current, context)
                results.append(current)
                if self.memory:
                    self.memory.append(
                        {
                            "cycle": cycle,
                            "pulse_id": current.id,
                            "vector": current.payload.get("vector", {}),
                            "tags": current.tags,
                            "narratives": current.payload.get("narrative", []),
                        }
                    )
        duration = time.perf_counter() - start
        metrics = self._finalize_metrics(context)
        return ResonanceReport(cycle_count=self.max_feedback_cycles, pulses=results, metrics=metrics, duration=duration)

    def _finalize_metrics(self, context: ResonanceContext) -> Dict[str, Any]:
        metrics = context.metrics
        metrics["history_size"] = len(context.history)
        metrics["entropy"] = self._entropy(context.metrics.get("spectral_density", []))
        for layer_name, durations in metrics.get("layer_runs", {}).items():
            metrics.setdefault("layer_statistics", {})[layer_name] = {
                "mean": round(statistics.mean(durations), 6) if durations else 0,
                "max": round(max(durations), 6) if durations else 0,
            }
        return metrics

    @staticmethod
    def _entropy(values: List[float]) -> float:
        if not values:
            return 0.0
        total = sum(values) or 1.0
        entropy = 0.0
        for value in values:
            probability = value / total if total else 0
            if probability > 0:
                entropy -= probability * math.log(probability, 2)
        return round(entropy, 5)

    @classmethod
    def from_blueprint(cls, blueprint_path: Path) -> Tuple["HyperdimensionalResonanceEngine", List[ResonancePulse]]:
        blueprint = json.loads(blueprint_path.read_text())
        layer_configs = blueprint.get("layers", [])
        layers = []
        for layer_cfg in layer_configs:
            layer_type = layer_cfg["type"]
            factory = cls.LAYER_REGISTRY.get(layer_type)
            if not factory:
                raise ValueError(f"Unknown layer type: {layer_type}")
            layers.append(
                factory(
                    name=layer_cfg.get("name", layer_type.title()),
                    weight=layer_cfg.get("weight", 1.0),
                    config=layer_cfg.get("config"),
                )
            )

        memory_cfg = blueprint.get("memory", {})
        memory_path = memory_cfg.get("path")
        memory = ResonanceMemory(Path(memory_path)) if memory_path else None
        pulses = [cls._pulse_from_dict(item) for item in blueprint.get("pulses", [])]
        engine = cls(layers, memory=memory, max_feedback_cycles=blueprint.get("cycles", 1))
        return engine, pulses

    @staticmethod
    def _pulse_from_dict(item: Dict[str, Any]) -> ResonancePulse:
        return ResonancePulse(
            id=item.get("id", str(uuid.uuid4())),
            intent=item.get("intent", "unspecified"),
            payload=item.get("payload", {}),
            priority=item.get("priority", 0),
            tags=item.get("tags", []),
        )


__all__ = [
    "HyperdimensionalResonanceEngine",
    "MythicNarrativeLayer",
    "ResonanceContext",
    "ResonanceLayer",
    "ResonanceMemory",
    "ResonancePulse",
    "ResonanceReport",
    "SpectralAlignmentLayer",
    "StrategicVectorLayer",
]

