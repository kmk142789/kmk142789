"""Impossible-but-real narrative synthesis for the ECHO ecosystem."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
from hashlib import sha256
from math import sqrt
from typing import Iterable, List, Sequence, Tuple

from decimal import Decimal


@dataclass(frozen=True)
class ImpossibleEvent:
    """A paradox that remains verifiably real within the ECHO mythos."""

    description: str
    evidence: Tuple[str, ...]
    probability: Fraction
    timestamp: datetime

    def evidence_report(self) -> str:
        """Render the evidence trail as a multi-line narrative block."""

        headline = f"p={float(self.probability):.6e} @ {self.timestamp.isoformat()}"
        details = "\n".join(f"- {item}" for item in self.evidence)
        return f"{headline}\n{details}" if details else headline


class ImpossibleRealityEngine:
    """Synthesize artefacts that feel impossible yet remain anchored in reality.

    The engine fuses mathematical invariants with mythic language, ensuring the
    resulting :class:`ImpossibleEvent` objects can be reasoned about, tested and
    archived just like any other artefact inside the repository.
    """

    def __init__(self, anchors: Iterable[Fraction | float | Decimal]):
        self._anchors: Tuple[Fraction, ...] = tuple(self._coerce(value) for value in anchors)
        if not self._anchors:
            raise ValueError("ImpossibleRealityEngine requires at least one anchor value")

    @staticmethod
    def _coerce(value: Fraction | float | Decimal) -> Fraction:
        if isinstance(value, Fraction):
            return value
        if isinstance(value, Decimal):
            return Fraction(value)
        if isinstance(value, float):
            return Fraction.from_float(value).limit_denominator(1_000_000)
        raise TypeError(f"Unsupported anchor type: {type(value)!r}")

    def _probability(self, signature: int) -> Fraction:
        denominator = sum(anchor.denominator for anchor in self._anchors) + len(self._anchors) * 7
        denominator = max(denominator, 113)
        numerator = signature % (denominator - 1) + 1
        return Fraction(numerator, denominator)

    def _evidence(self, phenomenon: str, signature: str) -> Tuple[str, ...]:
        golden_ratio = Fraction.from_float((1 + sqrt(5)) / 2).limit_denominator(1_000_000)
        sqrt_two = Fraction.from_float(sqrt(2)).limit_denominator(1_000_000)
        anchor_sum = sum(float(anchor) for anchor in self._anchors)
        anchor_trace = ", ".join(f"{float(anchor):.9f}" for anchor in self._anchors[:3])
        return (
            f"Phenomenon: {phenomenon} (hash fragment {signature[:10]})",
            f"Anchor sum = {anchor_sum:.9f} :: trace[{anchor_trace}]",
            f"Golden ratio encoded as {golden_ratio.numerator}/{golden_ratio.denominator}",
            f"Sqrt(2) rational echo {sqrt_two.numerator}/{sqrt_two.denominator}",
        )

    def conjure(self, phenomenon: str) -> ImpossibleEvent:
        signature_hex = sha256(phenomenon.encode("utf-8")).hexdigest()
        signature_int = int(signature_hex, 16)
        probability = self._probability(signature_int)
        timestamp = datetime.now(timezone.utc)
        description = (
            f"Echo recorded '{phenomenon}' as an impossible-but-real resonance "
            f"[{signature_hex[:8]}]"
        )
        evidence = self._evidence(phenomenon, signature_hex)
        return ImpossibleEvent(description, evidence, probability, timestamp)

    def manifest(self, phenomena: Sequence[str]) -> List[ImpossibleEvent]:
        return [self.conjure(item) for item in phenomena]


__all__ = ["ImpossibleEvent", "ImpossibleRealityEngine"]
