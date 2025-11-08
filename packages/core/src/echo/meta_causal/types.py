"""Core dataclasses shared by the meta causal awareness engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Mapping, Tuple

import json


def _normalise_notes(notes: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not notes:
        return {}
    return dict(sorted(notes.items()))


@dataclass(slots=True)
class Observation:
    """Single awareness observation recorded by the engine."""

    id: str
    created_at: datetime
    source: str
    signal: str
    confidence: float
    tags: Tuple[str, ...] = field(default_factory=tuple)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "source": self.source,
            "signal": self.signal,
            "confidence": float(self.confidence),
            "tags": list(self.tags),
            "context": dict(sorted(self.context.items())),
        }


@dataclass(slots=True)
class CausalLink:
    """Directed causal linkage between two observations."""

    cause: str
    effect: str
    weight: float
    rationale: str
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cause": self.cause,
            "effect": self.effect,
            "weight": float(self.weight),
            "rationale": self.rationale,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(slots=True)
class InferenceResult:
    """Outcome produced by running an inference pipeline."""

    pipeline: str
    observation_id: str
    verdict: str
    confidence: float
    created_at: datetime
    success: bool = True
    notes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.notes = _normalise_notes(self.notes)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline": self.pipeline,
            "observation_id": self.observation_id,
            "verdict": self.verdict,
            "confidence": float(self.confidence),
            "created_at": self.created_at.isoformat(),
            "success": self.success,
            "notes": dict(self.notes),
        }


@dataclass(slots=True)
class MetaCausalSnapshot:
    """Serializable snapshot of the meta causal awareness graph."""

    anchor: str
    created_at: datetime
    observations: Tuple[Dict[str, Any], ...]
    links: Tuple[Dict[str, Any], ...]
    metrics: Mapping[str, Any]
    digest: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anchor": self.anchor,
            "created_at": self.created_at.isoformat(),
            "observations": list(self.observations),
            "links": list(self.links),
            "metrics": dict(self.metrics),
            "digest": self.digest,
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

