from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AmplifyWeights:
    """Weighting factors for the Amplify Index calculation."""

    resonance: float = 0.24
    freshness_half_life: float = 0.12
    novelty_delta: float = 0.18
    cohesion: float = 0.18
    coverage: float = 0.16
    volatility: float = 0.12

    def as_dict(self) -> dict[str, float]:
        return {
            "resonance": self.resonance,
            "freshness_half_life": self.freshness_half_life,
            "novelty_delta": self.novelty_delta,
            "cohesion": self.cohesion,
            "coverage": self.coverage,
            "volatility": self.volatility,
        }

    def normalised(self) -> dict[str, float]:
        weights = self.as_dict()
        total = sum(weights.values())
        if total == 0:
            return {name: 0.0 for name in weights}
        return {name: value / total for name, value in weights.items()}


@dataclass(frozen=True)
class AmplifyConfig:
    """Runtime configuration for the amplification engine."""

    weights: AmplifyWeights = AmplifyWeights()
    gate_floor: float = 70.0
    log_path: Path = Path("state") / "amplify_log.jsonl"
    rolling_window: int = 3


__all__ = ["AmplifyConfig", "AmplifyWeights"]
