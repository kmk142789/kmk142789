"""Intent Gradient Interpreter (IGI).

The IGI reasons about *why* Echo should move from one context to another.
Given a flowing :class:`~echo.continuation_memory_engine.ContinuationPacket`
and a set of candidate contexts, it scores the transition options, preserving
continuity while surfacing the intent behind every move.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Mapping, Sequence

from .continuation_memory_engine import ContinuationPacket


@dataclass(frozen=True)
class ContextCandidate:
    """Represents a possible next context or router destination."""

    route: str
    objectives: Sequence[str]
    friction: float = 0.1
    metadata: Mapping[str, object] | None = None


@dataclass(frozen=True)
class IntentGradient:
    """Reasoned evaluation of a potential transition."""

    candidate: ContextCandidate
    score: float
    rationale: Sequence[str]

    def as_dict(self) -> Mapping[str, object]:
        return {
            "route": self.candidate.route,
            "score": self.score,
            "rationale": list(self.rationale),
            "friction": self.candidate.friction,
            "objectives": list(self.candidate.objectives),
        }


class IntentGradientInterpreter:
    """Lightweight reasoning layer that explains routing moves."""

    def __init__(self, *, continuity_bias: float = 0.2) -> None:
        self.continuity_bias = max(0.0, min(continuity_bias, 1.0))

    def _alignment_score(self, *, packet: ContinuationPacket, candidate: ContextCandidate) -> tuple[float, List[str]]:
        rationale: List[str] = []

        overlap = [obj for obj in candidate.objectives if obj.lower() in packet.dominant_signal.lower()]
        alignment = len(overlap)
        if overlap:
            rationale.append(f"Context aligns with dominant signal: {', '.join(overlap)}")

        if candidate.route in packet.breadcrumbs:
            alignment += self.continuity_bias
            rationale.append("Continuation bias applied (breadcrumb match)")

        stability = max(0.0, 1.0 - candidate.friction)
        alignment += stability
        rationale.append(f"Low friction path boosts stability score ({stability:.2f})")

        return alignment, rationale

    def interpret(self, *, packet: ContinuationPacket, candidates: Iterable[ContextCandidate]) -> List[IntentGradient]:
        gradients: List[IntentGradient] = []
        for candidate in candidates:
            alignment, rationale = self._alignment_score(packet=packet, candidate=candidate)
            score = round(packet.momentum + alignment, 4)
            rationale.append(f"Carried momentum: {packet.momentum:.2f}")
            gradients.append(IntentGradient(candidate=candidate, score=score, rationale=rationale))
        gradients.sort(key=lambda g: g.score, reverse=True)
        return gradients

    def select_next(self, *, packet: ContinuationPacket, candidates: Iterable[ContextCandidate]) -> IntentGradient | None:
        gradients = self.interpret(packet=packet, candidates=candidates)
        return gradients[0] if gradients else None


__all__ = [
    "ContextCandidate",
    "IntentGradient",
    "IntentGradientInterpreter",
]
