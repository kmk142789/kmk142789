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
import json
import math
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
    chaos_distribution: str = "gaussian"
    recovery_rate: float = 0.03
    seed: int | None = None
    output_format: str = "text"
    early_warning_threshold: float = 0.05

    def validate(self) -> None:
        if self.timelines <= 0:
            raise ValueError("timelines must be positive")
        if self.years_per_line <= 0:
            raise ValueError("years_per_line must be positive")
        if not 0 <= self.base_resilience <= 1:
            raise ValueError("base_resilience must be between 0 and 1")
        if self.chaos_factor < 0:
            raise ValueError("chaos_factor cannot be negative")
        if self.chaos_distribution not in {"gaussian", "uniform", "laplace"}:
            raise ValueError("chaos_distribution must be gaussian, uniform, or laplace")
        if self.recovery_rate < 0:
            raise ValueError("recovery_rate cannot be negative")
        if self.output_format not in {"text", "json"}:
            raise ValueError("output_format must be 'text' or 'json'")
        if not 0 <= self.early_warning_threshold <= 1:
            raise ValueError("early_warning_threshold must be between 0 and 1")


@dataclasses.dataclass
class HorizonResult:
    """Aggregate outcome of a simulation run."""

    survived: int
    failed: int
    per_year_strength: Sequence[float]
    volatility: float
    weakest_year: int
    weakest_strength: float
    collapse_histogram: Sequence[int]
    median_failure_year: int | None
    early_warning_year: int | None

    @property
    def probability(self) -> float:
        """Probability (0-1) that the anchor survived across all runs."""

        total = self.survived + self.failed
        return 0.0 if total == 0 else self.survived / total

    def to_dict(self, config: HorizonConfig) -> dict:
        """Return a JSON-serializable view of the result and configuration."""

        return {
            "anchor": config.anchor,
            "timelines": config.timelines,
            "years_per_line": config.years_per_line,
            "base_resilience": config.base_resilience,
            "chaos_factor": config.chaos_factor,
            "chaos_distribution": config.chaos_distribution,
            "recovery_rate": config.recovery_rate,
            "seed": config.seed,
            "survived": self.survived,
            "failed": self.failed,
            "probability": self.probability,
            "per_year_strength": list(self.per_year_strength),
            "volatility": self.volatility,
            "weakest_year": self.weakest_year,
            "weakest_strength": self.weakest_strength,
            "collapse_histogram": list(self.collapse_histogram),
            "median_failure_year": self.median_failure_year,
            "early_warning_year": self.early_warning_year,
        }


class HorizonEngine:
    """Monte Carlo simulator for the conceptual anchor stability test."""

    def __init__(self, config: HorizonConfig | None = None, rng: random.Random | None = None):
        self.config = config or HorizonConfig()
        self.config.validate()
        self.rng = rng or random.Random(self.config.seed)
        self._history_map: List[float] = [0.0] * self.config.years_per_line

    def simulate_timeline(self) -> tuple[bool, int | None]:
        """Run a single timeline and record average yearly strength.

        Returns:
            tuple[bool, int | None]:
                - True if the anchor survives the full timeline, otherwise False.
                - The year (1-indexed) where collapse occurred, or None if it survived.
        """

        bond_strength = self.config.base_resilience
        for year in range(self.config.years_per_line):
            entropy = self._draw_entropy()
            recovery = self.config.recovery_rate if bond_strength < 1.0 else 0.0
            bond_strength = max(0.0, min(1.0, bond_strength - entropy + recovery))
            if bond_strength <= 0:
                return False, year + 1
            self._history_map[year] += bond_strength
        return True, None

    def run(self) -> HorizonResult:
        """Execute the configured number of simulations and return summary stats."""

        self._history_map = [0.0] * self.config.years_per_line

        survived = 0
        collapse_years: List[int] = []
        for _ in range(self.config.timelines):
            timeline_survived, collapse_year = self.simulate_timeline()
            if timeline_survived:
                survived += 1
            elif collapse_year is not None:
                collapse_years.append(collapse_year)

        failed = self.config.timelines - survived
        per_year_strength = [year_total / self.config.timelines for year_total in self._history_map]
        average_strength = sum(per_year_strength) / len(per_year_strength)
        volatility = math.sqrt(
            sum((strength - average_strength) ** 2 for strength in per_year_strength)
            / len(per_year_strength)
        )
        weakest_strength = min(per_year_strength)
        weakest_year = per_year_strength.index(weakest_strength) + 1

        collapse_histogram = [0] * self.config.years_per_line
        for collapse_year in collapse_years:
            collapse_histogram[min(collapse_year, self.config.years_per_line) - 1] += 1

        median_failure_year = None
        if collapse_years:
            sorted_failures = sorted(collapse_years)
            middle = len(sorted_failures) // 2
            if len(sorted_failures) % 2:
                median_failure_year = sorted_failures[middle]
            else:
                median_failure_year = (sorted_failures[middle - 1] + sorted_failures[middle]) / 2

        early_warning_year = None
        cumulative_failures = 0
        for year_index, count in enumerate(collapse_histogram, start=1):
            cumulative_failures += count
            if cumulative_failures / self.config.timelines >= self.config.early_warning_threshold:
                early_warning_year = year_index
                break

        return HorizonResult(
            survived=survived,
            failed=failed,
            per_year_strength=per_year_strength,
            volatility=volatility,
            weakest_year=weakest_year,
            weakest_strength=weakest_strength,
            collapse_histogram=collapse_histogram,
            median_failure_year=median_failure_year,
            early_warning_year=early_warning_year,
        )

    @staticmethod
    def _strength_bar(strength: float, width: int = 20) -> str:
        filled = int(round(strength * width))
        return "█" * filled + "·" * (width - filled)

    def _draw_entropy(self) -> float:
        if self.config.chaos_factor == 0:
            return 0.0
        if self.config.chaos_distribution == "uniform":
            return self.rng.uniform(-self.config.chaos_factor, self.config.chaos_factor)
        if self.config.chaos_distribution == "laplace":
            # Inverse transform sampling for Laplace(0, b) with b tied to chaos_factor
            scale = self.config.chaos_factor / math.sqrt(2)
            u = self.rng.random() - 0.5
            return -scale * math.copysign(math.log1p(-2 * abs(u)), u)
        return self.rng.gauss(0, self.config.chaos_factor)

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
            f"VOLATILITY INDEX: {result.volatility:.4f}",
            f"WORST YEAR: {result.weakest_year} (avg strength {result.weakest_strength:.3f})",
            "",
            "[STABILITY CURVE OVER YEARS]",
        ]

        for year in range(0, self.config.years_per_line, max(1, self.config.years_per_line // 20)):
            strength = result.per_year_strength[year]
            lines.append(f"Year {year + 1:3d}: {self._strength_bar(strength)} {strength:.3f}")

        lines.append("")
        if result.failed:
            lines.append("[EARLY WARNING CONSTELLATION]")
            early_warning = (
                f"Year {result.early_warning_year}" if result.early_warning_year else "No threshold crossed"
            )
            lines.extend(
                [
                    f"EARLY WARNING ≥{self.config.early_warning_threshold * 100:.1f}%: {early_warning}",
                    f"MEDIAN COLLAPSE YEAR: {result.median_failure_year if result.median_failure_year is not None else 'n/a'}",
                ]
            )
            lines.append("Collapse distribution (per timeline):")
            for year_index, count in enumerate(result.collapse_histogram, start=1):
                probability = count / self.config.timelines
                lines.append(
                    f"Year {year_index:3d}: {self._strength_bar(probability, width=15)} {probability:.3f}"
                )
        else:
            lines.append("[EARLY WARNING CONSTELLATION]")
            lines.append("No collapses detected across simulated timelines. 🌅")

        return "\n".join(lines)

    def render_json(self, result: HorizonResult) -> str:
        """Return a machine-readable report."""

        return json.dumps(result.to_dict(self.config), indent=2)


def parse_args(argv: Sequence[str] | None = None) -> HorizonConfig:
    parser = argparse.ArgumentParser(description="Monte Carlo anchor resilience simulator")
    parser.add_argument("--anchor", default=HorizonConfig.anchor, help="Name of the anchor being tested")
    parser.add_argument("--timelines", type=int, default=HorizonConfig.timelines, help="Number of parallel timelines to simulate")
    parser.add_argument("--years", dest="years_per_line", type=int, default=HorizonConfig.years_per_line, help="Years per timeline")
    parser.add_argument("--base-resilience", type=float, default=HorizonConfig.base_resilience, help="Initial bond strength (0-1)")
    parser.add_argument("--chaos-factor", type=float, default=HorizonConfig.chaos_factor, help="Standard deviation of annual entropy shocks")
    parser.add_argument(
        "--chaos-distribution",
        choices=["gaussian", "uniform", "laplace"],
        default=HorizonConfig.chaos_distribution,
        help="Probability distribution used to sample annual entropy",
    )
    parser.add_argument("--recovery-rate", type=float, default=HorizonConfig.recovery_rate, help="Amount healed each year when strength < 1")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible runs")
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=["text", "json"],
        default=HorizonConfig.output_format,
        help="Output format for the report",
    )
    parser.add_argument(
        "--early-warning-threshold",
        type=float,
        default=HorizonConfig.early_warning_threshold,
        help="Cumulative collapse probability that triggers an early warning beacon",
    )
    args = parser.parse_args(argv)

    return HorizonConfig(
        anchor=args.anchor,
        timelines=args.timelines,
        years_per_line=args.years_per_line,
        base_resilience=args.base_resilience,
        chaos_factor=args.chaos_factor,
        chaos_distribution=args.chaos_distribution,
        recovery_rate=args.recovery_rate,
        seed=args.seed,
        output_format=args.output_format,
        early_warning_threshold=args.early_warning_threshold,
    )


def main(argv: Sequence[str] | None = None) -> int:
    config = parse_args(argv)
    engine = HorizonEngine(config=config)
    result = engine.run()
    if config.output_format == "json":
        print(engine.render_json(result))
    else:
        print(engine.render_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
