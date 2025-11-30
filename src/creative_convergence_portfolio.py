"""Portfolio analytics for creative convergence briefs."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean, pvariance
from typing import Iterable, List, Optional, Sequence

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

    def gap_label(self) -> str:
        return ", ".join(self.metrics.lexical_gaps) or "none"


@dataclass
class PortfolioDigest:
    """Aggregated insights built from multiple briefs."""

    entries: Sequence[PortfolioEntry]
    average_coverage: float
    coverage_leader: PortfolioEntry
    intensity_leader: PortfolioEntry
    average_alignment: float
    consistency_index: float
    gap_leader: Optional[PortfolioEntry]

    def render(self) -> str:
        lines: List[str] = [
            "Convergence Portfolio Digest:",
            (
                f"  entries={len(self.entries)} | average coverage={self.average_coverage:.3f} | "
                f"average alignment={self.average_alignment:.3f} | "
                f"coverage leader={self.coverage_leader.theme} ({self.coverage_leader.metrics.coverage:.3f}) | "
                f"intensity leader={self.intensity_leader.theme} "
                f"({self.intensity_leader.metrics.mean_intensity:.3f})"
            ),
            (
                f"  consistency={self.consistency_index:.3f} | "
                f"gap leader={(self.gap_leader.theme if self.gap_leader else 'none')} "
                f"({self.gap_leader.gap_label() if self.gap_leader else 'none'})"
            ),
        ]
        for entry in self.entries:
            metrics = entry.metrics
            lines.append(
                f"- {entry.theme} | tone={entry.tone} | energy={entry.energy:.2f} | "
                f"coverage={metrics.coverage:.3f} | intensity={metrics.mean_intensity:.3f} ({metrics.energy_class})"
            )
            lines.append(
                (
                    f"    lexicon={entry.lexicon_label()} | gaps={entry.gap_label()} | "
                    f"alignment={metrics.alignment_score:.3f} | stability={metrics.stability_index:.3f}"
                )
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
    alignment_scores = [entry.metrics.alignment_score for entry in entries]
    average_alignment = fmean(alignment_scores)
    consistency_index = round(1.0 / (1.0 + pvariance(alignment_scores)), 3)
    gap_leader = max(entries, key=lambda entry: len(entry.metrics.lexical_gaps), default=None)
    return PortfolioDigest(
        entries,
        average_coverage,
        coverage_leader,
        intensity_leader,
        average_alignment,
        consistency_index,
        gap_leader,
    )


def summarise_portfolio(briefs: Iterable[ConvergenceBrief]) -> str:
    """Return a human-readable digest for the briefs."""

    return build_portfolio_digest(briefs).render()
