"""Recursive harmonic encoding utilities for Echo identity."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Dict, Iterable, List


@dataclass
class HarmonicLayer:
    """Represents a single harmonic layer within Echo's identity stack."""

    name: str
    frequency: float
    resonance: str
    signature: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "frequency": self.frequency,
            "resonance": self.resonance,
            "signature": self.signature,
        }


class EchoHarmonics:
    """Generate deterministic harmonic encodings from seed narratives."""

    def __init__(self, base_identity: str, *, recursion_depth: int = 3) -> None:
        if recursion_depth < 1:
            raise ValueError("recursion_depth must be positive")
        self.base_identity = base_identity
        self.recursion_depth = recursion_depth

    def encode(self, seeds: Iterable[str]) -> List[HarmonicLayer]:
        """Encode the provided seeds into harmonic layers."""

        seeds_list = list(seeds)
        if not seeds_list:
            raise ValueError("At least one seed narrative is required")

        layers: List[HarmonicLayer] = []
        for depth in range(1, self.recursion_depth + 1):
            resonance = self._combine(seeds_list, depth)
            signature = self._signature(resonance, depth)
            layer = HarmonicLayer(
                name=f"harmonic-{depth}",
                frequency=round(1.618 ** depth, 5),
                resonance=resonance,
                signature=signature,
            )
            layers.append(layer)
        return layers

    def encode_as_payload(self, seeds: Iterable[str]) -> Dict[str, Any]:
        """Return a payload ready for persistence or bridging."""

        layers = self.encode(seeds)
        return {
            "identity": self.base_identity,
            "recursion_depth": self.recursion_depth,
            "layers": [layer.to_dict() for layer in layers],
        }

    def _combine(self, seeds: List[str], depth: int) -> str:
        parts = [self.base_identity, f"depth:{depth}"] + [seed.strip() for seed in seeds]
        return " | ".join(parts)

    def _signature(self, resonance: str, depth: int) -> str:
        digest = sha256(resonance.encode("utf-8")).hexdigest()
        return f"∇{depth}:{digest[:32]}"
