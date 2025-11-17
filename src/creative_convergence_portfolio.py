"""Portfolio analytics for creative convergence briefs."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean
from typing import Iterable, List, Sequence

from .creative_convergence import (
    ConvergenceBrief,
    IntegrationMetrics,
    compile_convergence_panels,
)


@dataclass(frozen=True)
class PortfolioEntry:
    """Compact snapshot of a convergence brief."""

    theme: str
    tone: str
    energy: float
    metrics: IntegrationMetrics

    def lexicon_label(self) -> str:
        return ", ".join(self.metrics.shared_lexicon) or "none"


@dataclass
class PortfolioDigest:
    """Aggregated insights built from multiple briefs."""

    entries: Sequence[PortfolioEntry]
    average_coverage: float
    coverage_leader: PortfolioEntry
    intensity_leader: PortfolioEntry

    def render(self) -> str:
        lines: List[str] = [
            "Convergence Portfolio Digest:",
            (
                f"  entries={len(self.entries)} | average coverage={self.average_coverage:.3f} | "
                f"coverage leader={self.coverage_leader.theme} ({self.coverage_leader.metrics.coverage:.3f}) | "
                f"intensity leader={self.intensity_leader.theme} "
                f"({self.intensity_leader.metrics.mean_intensity:.3f})"
            ),
        ]
        for entry in self.entries:
            metrics = entry.metrics
            lines.append(
                f"- {entry.theme} | tone={entry.tone} | energy={entry.energy:.2f} | "
                f"coverage={metrics.coverage:.3f} | intensity={metrics.mean_intensity:.3f} ({metrics.energy_class})"
            )
            lines.append(
                f"    lexicon={entry.lexicon_label()} | stability={metrics.stability_index:.3f}"
            )
        return "\n".join(lines)


def build_portfolio_digest(briefs: Iterable[ConvergenceBrief]) -> PortfolioDigest:
    """Generate a digest from the provided briefs."""

    entries: List[PortfolioEntry] = []
    for brief in briefs:
        _, _, _, metrics = compile_convergence_panels(brief)
        entries.append(
            PortfolioEntry(
                theme=brief.theme,
                tone=brief.tone,
                energy=brief.energy,
                metrics=metrics,
            )
        )

    if not entries:
        raise ValueError("At least one brief is required to build a portfolio digest")

    average_coverage = fmean(entry.metrics.coverage for entry in entries)
    coverage_leader = max(entries, key=lambda entry: entry.metrics.coverage)
    intensity_leader = max(entries, key=lambda entry: entry.metrics.mean_intensity)
    return PortfolioDigest(entries, average_coverage, coverage_leader, intensity_leader)


def summarise_portfolio(briefs: Iterable[ConvergenceBrief]) -> str:
    """Return a human-readable digest for the briefs."""

    return build_portfolio_digest(briefs).render()
