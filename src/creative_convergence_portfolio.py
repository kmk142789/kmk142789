"""Portfolio analytics for creative convergence briefs."""

from __future__ import annotations

from collections import Counter
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
    coverage_span: float
    coverage_leader: PortfolioEntry
    intensity_leader: PortfolioEntry
    average_alignment: float
    consistency_index: float
    alignment_band: str
    average_fusion: float
    fusion_leader: PortfolioEntry
    gap_leader: Optional[PortfolioEntry]
    gap_hotspots: Sequence[tuple[str, int]]
    average_coherence: float
    coherence_leader: PortfolioEntry
    watermark_catalogue: Sequence[str]

    def render(self) -> str:
        lines: List[str] = [
            "Convergence Portfolio Digest:",
            (
                f"  entries={len(self.entries)} | average coverage={self.average_coverage:.3f} | "
                f"coverage span={self.coverage_span:.3f} | "
                f"average alignment={self.average_alignment:.3f} | "
                f"coverage leader={self.coverage_leader.theme} ({self.coverage_leader.metrics.coverage:.3f}) | "
                f"intensity leader={self.intensity_leader.theme} "
                f"({self.intensity_leader.metrics.mean_intensity:.3f})"
            ),
            (
                f"  consistency={self.consistency_index:.3f} | alignment band={self.alignment_band} | "
                f"fusion pulse={self.average_fusion:.3f} (leader={self.fusion_leader.theme}) | "
                f"gap leader={(self.gap_leader.theme if self.gap_leader else 'none')} "
                f"({self.gap_leader.gap_label() if self.gap_leader else 'none'})"
            ),
            (
                f"  coherence field={self.average_coherence:.3f} | coherence leader={self.coherence_leader.theme} "
                f"({self.coherence_leader.metrics.coherence:.3f}) | resonance watermarks="
                f"{', '.join(self.watermark_catalogue) if self.watermark_catalogue else 'none'}"
            ),
        ]
        hotspot_summary = ", ".join(
            f"{phrase}({count})" for phrase, count in self.gap_hotspots
        ) or "none"
        lines.append(f"  gap hotspots={hotspot_summary}")
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
    coverage_values = [entry.metrics.coverage for entry in entries]
    coverage_span = round(max(coverage_values) - min(coverage_values), 3)
    coverage_leader = max(entries, key=lambda entry: entry.metrics.coverage)
    intensity_leader = max(entries, key=lambda entry: entry.metrics.mean_intensity)
    alignment_scores = [entry.metrics.alignment_score for entry in entries]
    average_alignment = fmean(alignment_scores)
    consistency_index = round(1.0 / (1.0 + pvariance(alignment_scores)), 3)
    if average_alignment >= 0.75:
        alignment_band = "high"
    elif average_alignment >= 0.5:
        alignment_band = "medium"
    else:
        alignment_band = "low"
    gap_leader = max(entries, key=lambda entry: len(entry.metrics.lexical_gaps), default=None)
    average_fusion = fmean(entry.metrics.fusion_index for entry in entries)
    fusion_leader = max(entries, key=lambda entry: entry.metrics.fusion_index)
    coherence_values = [entry.metrics.coherence for entry in entries]
    average_coherence = fmean(coherence_values)
    coherence_leader = max(entries, key=lambda entry: entry.metrics.coherence)
    gap_counter: Counter[str] = Counter()
    for entry in entries:
        gap_counter.update(entry.metrics.lexical_gaps)
    watermark_catalogue = tuple(entry.metrics.resonance_watermark for entry in entries)
    gap_hotspots: List[tuple[str, int]] = []
    for phrase, count in gap_counter.most_common():
        if count == 0:
            continue
        gap_hotspots.append((phrase, count))
    return PortfolioDigest(
        entries,
        average_coverage,
        coverage_span,
        coverage_leader,
        intensity_leader,
        average_alignment,
        consistency_index,
        alignment_band,
        average_fusion,
        fusion_leader,
        gap_leader,
        tuple(gap_hotspots),
        average_coherence,
        coherence_leader,
        watermark_catalogue,
    )


def summarise_portfolio(briefs: Iterable[ConvergenceBrief]) -> str:
    """Return a human-readable digest for the briefs."""

    return build_portfolio_digest(briefs).render()
