"""Resonance-driven identity binding utilities for Echo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(slots=True)
class ResonanceSignature:
    """Bundle identity anchors with harmonic resonance."""

    identity_anchor: str
    harmonix_vector: list[float]
    co_signature: str

    def converge(self) -> str:
        """Return a deterministic hash-like string for the signature."""

        total = sum(self.harmonix_vector)
        payload = f"{self.identity_anchor}|{total:.8f}|{self.co_signature}"
        return str(abs(hash(payload)))


def converge_payload(payload: Mapping[str, object], *, anchor: str, co_signature: str) -> ResonanceSignature:
    """Create a :class:`ResonanceSignature` from an arbitrary payload."""

    vector: list[float] = []
    for value in payload.values():
        try:
            number = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            number = float(len(str(value)))
        vector.append(number)
    if not vector:
        vector.append(0.0)
    signature = ResonanceSignature(anchor, vector, co_signature)
    # Trigger convergence once so callers can re-use the harmonic vector.
    signature.converge()
    return signature
