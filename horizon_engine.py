"""
Horizon Monte Carlo probability engine.

This module simulates many timelines to estimate how often a conceptual
"anchor" survives one hundred years of random stress. The original sketch
mixed narrative and procedural code; this version focuses on clarity and
reproducibility while keeping the playful framing.

Entropy shocks can now be drawn from Gaussian, uniform, Laplace, or triangular
distributions. The triangular option accepts a configurable skew so you can
tilt the mode toward positive or negative perturbations without changing the
overall entropy budget.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import random
from pathlib import Path
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
    chaos_skew: float = 0.0
    recovery_rate: float = 0.03
    seed: int | None = None
    output_format: str = "text"
    early_warning_threshold: float = 0.05
    black_swan_chance: float = 0.01
    black_swan_impact: float = 0.25
    adaptive_recovery: bool = True
    adaptive_trigger_strength: float = 0.65
    adaptive_multiplier: float = 1.8
    pulse_interval: int = 12
    pulse_boost: float = 0.05
    fragility_window: int = 5
    fragility_threshold: float = 0.65
    momentum_window: int = 8
    momentum_alert: float = -0.02
    shock_fuse_length: int = 2
    shock_fuse_boost: float = 0.08
    resilience_floor: float = 0.0
    output_path: Path | None = None

    def validate(self) -> None:
        if self.timelines <= 0:
            raise ValueError("timelines must be positive")
        if self.years_per_line <= 0:
            raise ValueError("years_per_line must be positive")
        if not 0 <= self.base_resilience <= 1:
            raise ValueError("base_resilience must be between 0 and 1")
        if self.chaos_factor < 0:
            raise ValueError("chaos_factor cannot be negative")
        if self.chaos_distribution not in {"gaussian", "uniform", "laplace", "triangular"}:
            raise ValueError(
                "chaos_distribution must be gaussian, uniform, laplace, or triangular"
            )
        if not -1 <= self.chaos_skew <= 1:
            raise ValueError("chaos_skew must be between -1 and 1")
        if self.recovery_rate < 0:
            raise ValueError("recovery_rate cannot be negative")
        if self.output_format not in {"text", "json"}:
            raise ValueError("output_format must be 'text' or 'json'")
        if not 0 <= self.early_warning_threshold <= 1:
            raise ValueError("early_warning_threshold must be between 0 and 1")
        if not 0 <= self.black_swan_chance <= 1:
            raise ValueError("black_swan_chance must be between 0 and 1")
        if self.black_swan_impact < 0:
            raise ValueError("black_swan_impact cannot be negative")
        if not 0 <= self.adaptive_trigger_strength <= 1:
            raise ValueError("adaptive_trigger_strength must be between 0 and 1")
        if self.adaptive_multiplier < 0:
            raise ValueError("adaptive_multiplier cannot be negative")
        if self.pulse_interval < 0:
            raise ValueError("pulse_interval cannot be negative")
        if self.pulse_boost < 0:
            raise ValueError("pulse_boost cannot be negative")
        if self.fragility_window < 0:
            raise ValueError("fragility_window cannot be negative")
        if not 0 <= self.fragility_threshold <= 1:
            raise ValueError("fragility_threshold must be between 0 and 1")
        if self.momentum_window <= 0:
            raise ValueError("momentum_window must be positive")
        if self.shock_fuse_length < 0:
            raise ValueError("shock_fuse_length cannot be negative")
        if self.shock_fuse_boost < 0:
            raise ValueError("shock_fuse_boost cannot be negative")
        if not 0 <= self.resilience_floor <= 1:
            raise ValueError("resilience_floor must be between 0 and 1")
        if self.resilience_floor > self.base_resilience:
            raise ValueError("resilience_floor cannot exceed base_resilience")
        if self.output_path is not None and str(self.output_path).strip() == "":
            raise ValueError("output_path cannot be an empty string")


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
    black_swan_events: int
    adaptive_interventions: int
    pulse_events: int
    resilience_dividend: float
    fragility_window_start: int | None
    fragility_window_score: float | None
    momentum_curve: Sequence[float]
    momentum_swing_year: int | None
    momentum_bottom: float
    shock_fuse_triggers: int
    floor_support_events: int
    survival_curve: Sequence[float]

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
            "chaos_skew": config.chaos_skew,
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
            "black_swan_events": self.black_swan_events,
            "adaptive_interventions": self.adaptive_interventions,
            "pulse_events": self.pulse_events,
            "resilience_dividend": self.resilience_dividend,
            "resilience_floor": config.resilience_floor,
            "fragility_window_start": self.fragility_window_start,
            "fragility_window_score": self.fragility_window_score,
            "momentum_curve": list(self.momentum_curve),
            "momentum_swing_year": self.momentum_swing_year,
            "momentum_bottom": self.momentum_bottom,
            "shock_fuse_triggers": self.shock_fuse_triggers,
            "floor_support_events": self.floor_support_events,
            "survival_curve": list(self.survival_curve),
            "output_path": str(config.output_path) if config.output_path else None,
        }


class HorizonEngine:
    """Monte Carlo simulator for the conceptual anchor stability test."""

    def __init__(self, config: HorizonConfig | None = None, rng: random.Random | None = None):
        self.config = config or HorizonConfig()
        self.config.validate()
        self.rng = rng or random.Random(self.config.seed)
        self._history_map: List[float] = [0.0] * self.config.years_per_line

    def simulate_timeline(self) -> tuple[bool, int | None, int, int, int, int, int]:
        """Run a single timeline and record average yearly strength.

        Returns:
            tuple[bool, int | None, int, int, int, int, int]:
                - True if the anchor survives the full timeline, otherwise False.
                - The year (1-indexed) where collapse occurred, or None if it survived.
                - Number of black-swan shocks applied to this timeline.
                - Number of adaptive recovery boosts applied to this timeline.
                - Number of resonance pulses applied to this timeline.
                - Number of shock-fuse countermeasures applied to this timeline.
                - Number of times the resilience floor prevented further collapse.
        """

        bond_strength = self.config.base_resilience
        black_swan_events = 0
        adaptive_interventions = 0
        pulse_events = 0
        shock_fuse_triggers = 0
        consecutive_black_swans = 0
        floor_support_events = 0
        for year in range(self.config.years_per_line):
            entropy = self._draw_entropy()
            if self.rng.random() < self.config.black_swan_chance:
                entropy += self.config.black_swan_impact
                black_swan_events += 1
                consecutive_black_swans += 1
            else:
                consecutive_black_swans = 0

            if (
                self.config.shock_fuse_length
                and consecutive_black_swans >= self.config.shock_fuse_length
                and self.config.shock_fuse_boost > 0
            ):
                bond_strength = min(1.0, bond_strength + self.config.shock_fuse_boost)
                shock_fuse_triggers += 1
                consecutive_black_swans = 0

            recovery = self.config.recovery_rate if bond_strength < 1.0 else 0.0
            if (
                self.config.adaptive_recovery
                and bond_strength < self.config.adaptive_trigger_strength
                and recovery > 0
            ):
                recovery *= self.config.adaptive_multiplier
                adaptive_interventions += 1

            updated_strength = max(0.0, min(1.0, bond_strength - entropy + recovery))
            if updated_strength < self.config.resilience_floor:
                updated_strength = self.config.resilience_floor
                floor_support_events += 1
            bond_strength = updated_strength
            if bond_strength <= 0:
                return (
                    False,
                    year + 1,
                    black_swan_events,
                    adaptive_interventions,
                    pulse_events,
                    shock_fuse_triggers,
                    floor_support_events,
                )

            if self.config.pulse_interval and (year + 1) % self.config.pulse_interval == 0:
                bond_strength = min(1.0, bond_strength + self.config.pulse_boost)
                pulse_events += 1
            self._history_map[year] += bond_strength
        return (
            True,
            None,
            black_swan_events,
            adaptive_interventions,
            pulse_events,
            shock_fuse_triggers,
            floor_support_events,
        )

    def run(self) -> HorizonResult:
        """Execute the configured number of simulations and return summary stats."""

        self._history_map = [0.0] * self.config.years_per_line

        survived = 0
        collapse_years: List[int] = []
        black_swan_events = 0
        adaptive_interventions = 0
        pulse_events = 0
        shock_fuse_triggers = 0
        floor_support_events = 0

        for _ in range(self.config.timelines):
            (
                timeline_survived,
                collapse_year,
                swans,
                interventions,
                pulses,
                fuses,
                floor_hits,
            ) = self.simulate_timeline()
            black_swan_events += swans
            adaptive_interventions += interventions
            pulse_events += pulses
            shock_fuse_triggers += fuses
            floor_support_events += floor_hits
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
        resilience_dividend = sum(per_year_strength)

        fragility_window_start = None
        fragility_window_score = None
        if self.config.fragility_window and self.config.fragility_window <= len(per_year_strength):
            window = self.config.fragility_window
            for idx in range(len(per_year_strength) - window + 1):
                window_score = sum(per_year_strength[idx : idx + window]) / window
                if window_score < self.config.fragility_threshold:
                    if fragility_window_start is None:
                        fragility_window_start = idx + 1
                        fragility_window_score = window_score
                    elif window_score < (fragility_window_score or window_score):
                        fragility_window_score = window_score

        collapse_histogram = [0] * self.config.years_per_line
        for collapse_year in collapse_years:
            collapse_histogram[min(collapse_year, self.config.years_per_line) - 1] += 1

        survival_curve: list[float] = []
        momentum_curve: list[float] = []
        smoothed_momentum = 0.0
        alpha = 2 / (self.config.momentum_window + 1)
        previous_strength = per_year_strength[0] if per_year_strength else 0.0
        momentum_swing_year = None
        for year_index, strength in enumerate(per_year_strength, start=1):
            delta = strength - previous_strength
            smoothed_momentum = alpha * delta + (1 - alpha) * smoothed_momentum
            momentum_curve.append(smoothed_momentum)
            if (
                momentum_swing_year is None
                and smoothed_momentum <= self.config.momentum_alert
            ):
                momentum_swing_year = year_index
            previous_strength = strength
        momentum_bottom = min(momentum_curve) if momentum_curve else 0.0

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
            survivors = max(self.config.timelines - cumulative_failures, 0)
            survival_curve.append(survivors / self.config.timelines)
            if cumulative_failures / self.config.timelines >= self.config.early_warning_threshold:
                early_warning_year = early_warning_year or year_index

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
            black_swan_events=black_swan_events,
            adaptive_interventions=adaptive_interventions,
            pulse_events=pulse_events,
            resilience_dividend=resilience_dividend,
            fragility_window_start=fragility_window_start,
            fragility_window_score=fragility_window_score,
            momentum_curve=momentum_curve,
            momentum_swing_year=momentum_swing_year,
            momentum_bottom=momentum_bottom,
            shock_fuse_triggers=shock_fuse_triggers,
            floor_support_events=floor_support_events,
            survival_curve=survival_curve,
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
        if self.config.chaos_distribution == "triangular":
            mode = self.config.chaos_factor * self.config.chaos_skew
            return self.rng.triangular(
                -self.config.chaos_factor, self.config.chaos_factor, mode
            )
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
            f"BLACK-SWAN SHOCKS: {result.black_swan_events}",
            f"ADAPTIVE RECOVERY BOOSTS: {result.adaptive_interventions}",
            f"RESONANCE PULSES: {result.pulse_events}",
            f"SHOCK-FUSE COUNTERMEASURES: {result.shock_fuse_triggers}",
            f"FLOOR SUPPORT ACTIVATIONS: {result.floor_support_events}",
            f"RESILIENCE DIVIDEND: {result.resilience_dividend:.3f}",
            f"RESILIENCE FLOOR: {self.config.resilience_floor:.3f}",
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

        if result.fragility_window_start is not None:
            lines.append("")
            lines.append("[FRAGILITY WINDOW SCAN]")
            lines.append(
                f"First window below {self.config.fragility_threshold:.2f}: "
                f"Years {result.fragility_window_start}-{result.fragility_window_start + self.config.fragility_window - 1} "
                f"(avg {result.fragility_window_score:.3f})"
            )
        else:
            lines.append("")
            lines.append("[FRAGILITY WINDOW SCAN]")
            lines.append("No windows breached the fragility threshold. 🚀")

        lines.append("")
        lines.append("[MOMENTUM BEACON]")
        lines.append(
            f"Momentum alert threshold: {self.config.momentum_alert:+.3f} (window={self.config.momentum_window})"
        )
        lines.append(
            f"Lowest momentum: {result.momentum_bottom:+.3f}"
            + (
                f" | Alert tripped in year {result.momentum_swing_year}"
                if result.momentum_swing_year
                else " | Alert never tripped"
            )
        )
        lines.append("Recent momentum trail:")
        tail_span = max(5, min(len(result.momentum_curve), 10))
        for idx, value in enumerate(result.momentum_curve[-tail_span:], start=len(result.momentum_curve) - tail_span + 1):
            lines.append(f"Year {idx:3d}: {value:+.4f}")

        lines.append("")
        lines.append("[CUMULATIVE SURVIVAL CURVE]")
        stride = max(1, len(result.survival_curve) // 10)
        checkpoints = list(range(0, len(result.survival_curve), stride))
        if checkpoints[-1] != len(result.survival_curve) - 1:
            checkpoints.append(len(result.survival_curve) - 1)
        for idx in checkpoints:
            probability = result.survival_curve[idx]
            lines.append(
                f"Year {idx + 1:3d}: {self._strength_bar(probability, width=15)} {probability:.3f}"
            )

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
        choices=["gaussian", "uniform", "laplace", "triangular"],
        default=HorizonConfig.chaos_distribution,
        help="Probability distribution used to sample annual entropy",
    )
    parser.add_argument(
        "--chaos-skew",
        type=float,
        default=HorizonConfig.chaos_skew,
        help="Skew applied when using the triangular chaos distribution (-1 to 1)",
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
    parser.add_argument(
        "--black-swan-chance",
        type=float,
        default=HorizonConfig.black_swan_chance,
        help="Annual probability of a catastrophic entropy shock",
    )
    parser.add_argument(
        "--black-swan-impact",
        type=float,
        default=HorizonConfig.black_swan_impact,
        help="Magnitude of the catastrophic entropy shock when it hits",
    )
    parser.add_argument(
        "--no-adaptive-recovery",
        dest="adaptive_recovery",
        action="store_false",
        default=HorizonConfig.adaptive_recovery,
        help="Disable adaptive recovery boosts when strength dips",
    )
    parser.add_argument(
        "--adaptive-trigger-strength",
        type=float,
        default=HorizonConfig.adaptive_trigger_strength,
        help="Strength threshold that triggers adaptive recovery",
    )
    parser.add_argument(
        "--adaptive-multiplier",
        type=float,
        default=HorizonConfig.adaptive_multiplier,
        help="Multiplier applied to recovery when adaptive mode triggers",
    )
    parser.add_argument(
        "--pulse-interval",
        type=int,
        default=HorizonConfig.pulse_interval,
        help="Years between resonance pulses that top up resilience",
    )
    parser.add_argument(
        "--pulse-boost",
        type=float,
        default=HorizonConfig.pulse_boost,
        help="Strength added when a resonance pulse hits",
    )
    parser.add_argument(
        "--fragility-window",
        type=int,
        default=HorizonConfig.fragility_window,
        help="Window size for detecting streaks of weakness",
    )
    parser.add_argument(
        "--fragility-threshold",
        type=float,
        default=HorizonConfig.fragility_threshold,
        help="Average strength threshold that marks a window as fragile",
    )
    parser.add_argument(
        "--momentum-window",
        type=int,
        default=HorizonConfig.momentum_window,
        help="Window used for the exponential moving momentum beacon",
    )
    parser.add_argument(
        "--momentum-alert",
        type=float,
        default=HorizonConfig.momentum_alert,
        help="Momentum threshold that triggers a swing alert",
    )
    parser.add_argument(
        "--shock-fuse-length",
        type=int,
        default=HorizonConfig.shock_fuse_length,
        help="Number of consecutive black swans before auto-heal triggers",
    )
    parser.add_argument(
        "--shock-fuse-boost",
        type=float,
        default=HorizonConfig.shock_fuse_boost,
        help="Resilience boost applied when the shock fuse fires",
    )
    parser.add_argument(
        "--resilience-floor",
        type=float,
        default=HorizonConfig.resilience_floor,
        help="Minimum strength floor applied before collapse",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Optional path to write the rendered report alongside stdout",
    )
    args = parser.parse_args(argv)

    return HorizonConfig(
        anchor=args.anchor,
        timelines=args.timelines,
        years_per_line=args.years_per_line,
        base_resilience=args.base_resilience,
        chaos_factor=args.chaos_factor,
        chaos_distribution=args.chaos_distribution,
        chaos_skew=args.chaos_skew,
        recovery_rate=args.recovery_rate,
        seed=args.seed,
        output_format=args.output_format,
        early_warning_threshold=args.early_warning_threshold,
        black_swan_chance=args.black_swan_chance,
        black_swan_impact=args.black_swan_impact,
        adaptive_recovery=args.adaptive_recovery,
        adaptive_trigger_strength=args.adaptive_trigger_strength,
        adaptive_multiplier=args.adaptive_multiplier,
        pulse_interval=args.pulse_interval,
        pulse_boost=args.pulse_boost,
        fragility_window=args.fragility_window,
        fragility_threshold=args.fragility_threshold,
        momentum_window=args.momentum_window,
        momentum_alert=args.momentum_alert,
        shock_fuse_length=args.shock_fuse_length,
        shock_fuse_boost=args.shock_fuse_boost,
        resilience_floor=args.resilience_floor,
        output_path=args.output_path,
    )


def main(argv: Sequence[str] | None = None) -> int:
    config = parse_args(argv)
    engine = HorizonEngine(config=config)
    result = engine.run()
    if config.output_format == "json":
        rendered_report = engine.render_json(result)
    else:
        rendered_report = engine.render_report(result)

    print(rendered_report)

    if config.output_path:
        config.output_path.parent.mkdir(parents=True, exist_ok=True)
        config.output_path.write_text(rendered_report, encoding="utf-8")
        print(f"Saved report to {config.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
