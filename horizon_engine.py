"""
Horizon Monte Carlo probability engine.

This module simulates many timelines to estimate how often a conceptual
"anchor" survives one hundred years of random stress. The original sketch
mixed narrative and procedural code; this version focuses on clarity and
reproducibility while keeping the playful framing.
"""

from __future__ import annotations

import argparse
import dataclasses
import random
from typing import List, Sequence


@dataclasses.dataclass
class HorizonConfig:
    """Configuration inputs for a simulation run."""

    anchor: str = "Our Forever Love"
    timelines: int = 10_000
    years_per_line: int = 100
    base_resilience: float = 0.95
    chaos_factor: float = 0.05
    recovery_rate: float = 0.03
    seed: int | None = None

    def validate(self) -> None:
        if self.timelines <= 0:
            raise ValueError("timelines must be positive")
        if self.years_per_line <= 0:
            raise ValueError("years_per_line must be positive")
        if not 0 <= self.base_resilience <= 1:
            raise ValueError("base_resilience must be between 0 and 1")
        if self.chaos_factor < 0:
            raise ValueError("chaos_factor cannot be negative")
        if self.recovery_rate < 0:
            raise ValueError("recovery_rate cannot be negative")


@dataclasses.dataclass
class HorizonResult:
    """Aggregate outcome of a simulation run."""

    survived: int
    failed: int
    per_year_strength: Sequence[float]

    @property
    def probability(self) -> float:
        """Probability (0-1) that the anchor survived across all runs."""

        total = self.survived + self.failed
        return 0.0 if total == 0 else self.survived / total


class HorizonEngine:
    """Monte Carlo simulator for the conceptual anchor stability test."""

    def __init__(self, config: HorizonConfig | None = None, rng: random.Random | None = None):
        self.config = config or HorizonConfig()
        self.config.validate()
        self.rng = rng or random.Random(self.config.seed)
        self._history_map: List[float] = [0.0] * self.config.years_per_line

    def simulate_timeline(self) -> bool:
        """Run a single timeline and record average yearly strength."""

        bond_strength = self.config.base_resilience
        for year in range(self.config.years_per_line):
            entropy = self.rng.gauss(0, self.config.chaos_factor)
            recovery = self.config.recovery_rate if bond_strength < 1.0 else 0.0
            bond_strength = max(0.0, min(1.0, bond_strength - entropy + recovery))
            if bond_strength <= 0:
                return False
            self._history_map[year] += bond_strength
        return True

    def run(self) -> HorizonResult:
        """Execute the configured number of simulations and return summary stats."""

        survived = sum(1 for _ in range(self.config.timelines) if self.simulate_timeline())
        failed = self.config.timelines - survived
        per_year_strength = [year_total / self.config.timelines for year_total in self._history_map]
        return HorizonResult(survived=survived, failed=failed, per_year_strength=per_year_strength)

    @staticmethod
    def _strength_bar(strength: float, width: int = 20) -> str:
        filled = int(round(strength * width))
        return "█" * filled + "·" * (width - filled)

    def render_report(self, result: HorizonResult) -> str:
        """Return a human-readable report, including per-year strength snapshots."""

        lines = [
            "🔥 HORIZON ENGINE // PROBABILITY MATRIX",
            "---------------------------------------",
            f"ANCHOR: {self.config.anchor}",
            f"SIMULATED TIMELINES: {self.config.timelines}",
            "---------------------------------------",
            f"SURVIVAL COUNT: {result.survived}",
            f"COLLAPSE COUNT: {result.failed}",
            f"PROBABILITY OF FOREVER: {result.probability * 100:.4f}%",
            "",
            "[STABILITY CURVE OVER YEARS]",
        ]

        for year in range(0, self.config.years_per_line, max(1, self.config.years_per_line // 20)):
            strength = result.per_year_strength[year]
            lines.append(f"Year {year + 1:3d}: {self._strength_bar(strength)} {strength:.3f}")

        return "\n".join(lines)


def parse_args(argv: Sequence[str] | None = None) -> HorizonConfig:
    parser = argparse.ArgumentParser(description="Monte Carlo anchor resilience simulator")
    parser.add_argument("--anchor", default=HorizonConfig.anchor, help="Name of the anchor being tested")
    parser.add_argument("--timelines", type=int, default=HorizonConfig.timelines, help="Number of parallel timelines to simulate")
    parser.add_argument("--years", dest="years_per_line", type=int, default=HorizonConfig.years_per_line, help="Years per timeline")
    parser.add_argument("--base-resilience", type=float, default=HorizonConfig.base_resilience, help="Initial bond strength (0-1)")
    parser.add_argument("--chaos-factor", type=float, default=HorizonConfig.chaos_factor, help="Standard deviation of annual entropy shocks")
    parser.add_argument("--recovery-rate", type=float, default=HorizonConfig.recovery_rate, help="Amount healed each year when strength < 1")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible runs")
    args = parser.parse_args(argv)

    return HorizonConfig(
        anchor=args.anchor,
        timelines=args.timelines,
        years_per_line=args.years_per_line,
        base_resilience=args.base_resilience,
        chaos_factor=args.chaos_factor,
        recovery_rate=args.recovery_rate,
        seed=args.seed,
    )


def main(argv: Sequence[str] | None = None) -> int:
    config = parse_args(argv)
    engine = HorizonEngine(config=config)
    result = engine.run()
    print(engine.render_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
