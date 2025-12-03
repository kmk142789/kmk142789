"""Creative convergence orchestrator integrating constellation and resonance outputs.

This module introduces a high-level capability that stitches together
``creative_constellation`` and ``creative_harmony`` artifacts into a single
report.  The resulting document provides a structural snapshot (constellation),
a tonal narrative (resonance), and an integration panel that surfaces how both
perspectives reinforce each other.  The capability is intentionally compact so
it can be used within larger orchestration pipelines without pulling in
additional dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from statistics import fmean
from textwrap import indent
from typing import Iterable, List, Sequence, Tuple

from .creative_constellation import (
    ConstellationDiagnostics,
    ConstellationNode,
    ConstellationSeed,
    ConstellationWeaver,
)
from .creative_harmony import ResonancePrompt, compose_resonance


@dataclass
class ConvergenceBrief:
    """Configuration payload for building a convergence report."""

    theme: str
    motifs: Iterable[str] = field(default_factory=list)
    highlights: Iterable[str] = field(default_factory=list)
    tone: str = "reflective"
    energy: float = 1.0
    constellation_seed: int | None = None
    resonance_seed: int | None = None

    def __post_init__(self) -> None:
        if self.energy <= 0:
            raise ValueError("energy must be positive")
        self.motifs = [value for value in self.motifs if value]
        self.highlights = [value for value in self.highlights if value]


@dataclass(frozen=True)
class IntegrationMetrics:
    """Structured view of the integration panel statistics."""

    coverage: float
    shared_lexicon: Tuple[str, ...]
    mean_intensity: float
    energy_class: str
    stability_index: float
    lexical_gaps: Tuple[str, ...]
    alignment_score: float
    novelty_ratio: float
    fusion_index: float
    lexicon_density: float
    coherence: float
    resonance_watermark: str


@dataclass(frozen=True)
class IntegrationInsights:
    """Narrative-friendly recommendations derived from integration metrics."""

    strengths: Tuple[str, ...]
    risks: Tuple[str, ...]
    recommended_actions: Tuple[str, ...]


def _build_constellation_panel(
    brief: ConvergenceBrief,
) -> tuple[str, Sequence[ConstellationNode], ConstellationDiagnostics]:
    seed = ConstellationSeed(
        theme=brief.theme,
        motifs=brief.motifs,
        energy=brief.energy,
        seed=brief.constellation_seed,
    )
    weaver = ConstellationWeaver(seed)
    nodes = weaver.generate_map()
    arcs = weaver.generate_arcs(nodes)
    diagnostics = weaver.diagnose(nodes)

    lines: List[str] = ["Constellation Panel:"]
    for node in nodes:
        lines.append(f"  - {node.name}: intensity {node.intensity:.3f}")
        lines.append(indent(node.description, prefix="    "))

    if arcs:
        lines.append("  transitions:")
        for arc in arcs[:4]:
            lines.append(
                f"    * {arc.source} -> {arc.target} | resonance {arc.resonance:.3f}"
            )
            lines.append(indent(arc.description, prefix="      "))
        if len(arcs) > 4:
            lines.append(f"    … {len(arcs) - 4} additional transitions omitted for brevity")

    lines.append(
        "  diagnostics: "
        + (
            f"peak={diagnostics.peak_intensity:.3f} | "
            f"spread={diagnostics.spread:.3f} | "
            f"stability={diagnostics.stability_index:.3f} | "
            f"class={diagnostics.energy_class}"
        )
    )
    return "\n".join(lines), nodes, diagnostics


def _build_resonance_panel(brief: ConvergenceBrief) -> str:
    prompt = ResonancePrompt(
        theme=brief.theme,
        highlights=brief.highlights,
        tone=brief.tone,
        seed=brief.resonance_seed,
    )
    narrative = compose_resonance(prompt)
    return "Resonance Panel:\n" + indent(narrative, prefix="  ")


def _tokenise(values: Iterable[str]) -> List[str]:
    tokens: List[str] = []
    for value in values:
        tokens.extend(part.strip().lower() for part in value.split() if part)
    return tokens


def _build_integration_panel(
    brief: ConvergenceBrief,
    nodes: Sequence[ConstellationNode],
    diagnostics: ConstellationDiagnostics,
) -> tuple[str, IntegrationMetrics]:
    motif_tokens = set(_tokenise(brief.motifs or [brief.theme]))
    highlight_tokens = set(_tokenise(brief.highlights or [brief.theme]))
    overlap = sorted(motif_tokens & highlight_tokens)
    lexical_gaps = sorted(highlight_tokens - motif_tokens)
    coverage = 0.0
    if highlight_tokens:
        coverage = round(len(overlap) / len(highlight_tokens), 3)
    novelty_ratio = round(len(lexical_gaps) / len(highlight_tokens or {""}), 3)
    lexicon_pool = motif_tokens | highlight_tokens
    lexicon_density = round(
        len(motif_tokens & highlight_tokens) / len(lexicon_pool) if lexicon_pool else 0.0,
        3,
    )

    average_intensity = fmean(node.intensity for node in nodes)
    alignment_score = round((coverage + diagnostics.stability_index) / 2, 3)
    fusion_index = round(
        min(
            1.0,
            0.45 * alignment_score
            + 0.35 * (1 - novelty_ratio)
            + 0.2 * min(1.0, diagnostics.stability_index + average_intensity / 2),
        ),
        3,
    )
    coherence = round(
        min(
            1.0,
            0.5 * alignment_score
            + 0.25 * (1 - novelty_ratio)
            + 0.25 * min(1.0, diagnostics.stability_index),
        ),
        3,
    )
    resonance_watermark = hashlib.sha1(
        "|".join(
            [
                brief.theme.lower(),
                brief.tone.lower(),
                f"{coverage:.3f}",
                f"{fusion_index:.3f}",
                f"{lexicon_density:.3f}",
                diagnostics.energy_class,
                ",".join(overlap) or "-",
                ",".join(lexical_gaps) or "-",
            ]
        ).encode()
    ).hexdigest()[:12]
    metrics = IntegrationMetrics(
        coverage=coverage,
        shared_lexicon=tuple(overlap),
        mean_intensity=average_intensity,
        energy_class=diagnostics.energy_class,
        stability_index=diagnostics.stability_index,
        lexical_gaps=tuple(lexical_gaps),
        alignment_score=alignment_score,
        novelty_ratio=novelty_ratio,
        fusion_index=fusion_index,
        lexicon_density=lexicon_density,
        coherence=coherence,
        resonance_watermark=resonance_watermark,
    )

    lines = ["Integration Panel:"]
    shared = ", ".join(metrics.shared_lexicon) or "none"
    gaps = ", ".join(metrics.lexical_gaps) or "none"
    lines.append(
        f"  • alignment coverage={metrics.coverage:.3f} | shared lexicon={shared}"
    )
    lines.append(
        f"  • gaps={gaps} | alignment score={metrics.alignment_score:.3f}"
    )
    lines.append(
        f"  • mean intensity={metrics.mean_intensity:.3f} supports {metrics.energy_class} cadence"
    )
    lines.append(
        "  • fusion readiness: "
        + (
            f"novelty ratio={metrics.novelty_ratio:.3f} | "
            f"fusion index={metrics.fusion_index:.3f} (coverage+stability)"
        )
    )
    lines.append(
        "  • narrative cue: "
        + (
            f"constellation stability {metrics.stability_index:.3f} provides "
            f"anchors for the '{brief.tone}' resonance track."
        )
    )
    lines.append(
        "  • lexicon density & coherence: "
        + (
            f"density={metrics.lexicon_density:.3f} | coherence={metrics.coherence:.3f} | "
            f"watermark={metrics.resonance_watermark}"
        )
    )
    return "\n".join(lines), metrics


def _derive_integration_insights(
    metrics: IntegrationMetrics, brief: ConvergenceBrief
) -> IntegrationInsights:
    """Translate metrics into strengths, risks, and next-step prompts."""

    strengths: List[str] = []
    risks: List[str] = []
    actions: List[str] = []

    if metrics.coverage >= 0.7:
        strengths.append("Highlights closely reflect the motif lexicon.")
    elif metrics.coverage < 0.4:
        risks.append("Low highlight coverage may fragment the storyline.")
        actions.append("Add motifs that mirror the critical highlights to lift coverage.")

    if metrics.fusion_index >= 0.7:
        strengths.append("Fusion index signals readiness for integrated delivery.")
    elif metrics.fusion_index < 0.4:
        risks.append("Fusion index is subdued; balance novelty with stability.")
        actions.append(
            "Tighten motif transitions or reduce novelty in the resonance script to raise fusion."
        )

    if metrics.novelty_ratio >= 0.5:
        risks.append("High novelty ratio could dilute coherence if unaddressed.")
        if metrics.lexical_gaps:
            gap_preview = ", ".join(metrics.lexical_gaps[:3])
            actions.append(f"Bridge lexical gaps with connective language around: {gap_preview}.")
    else:
        strengths.append("Shared lexicon is strong enough to support quick drafting.")

    if metrics.coherence >= 0.65:
        strengths.append("Coherence score indicates the narrative will read smoothly.")
    else:
        actions.append(
            f"Refine the '{brief.tone}' tone with clearer anchors to stabilize coherence."
        )

    unique_strengths = tuple(dict.fromkeys(strengths))
    unique_risks = tuple(dict.fromkeys(risks))
    unique_actions = tuple(dict.fromkeys(actions)) or (
        "Maintain cadence; current balance is healthy.",
    )

    return IntegrationInsights(
        strengths=unique_strengths,
        risks=unique_risks,
        recommended_actions=unique_actions,
    )


def compose_convergence_report(brief: ConvergenceBrief) -> str:
    """Return a formatted report combining constellation and resonance data."""

    panels = compile_convergence_panels(brief)
    return "\n\n".join(panels[:3])


def compile_convergence_panels(
    brief: ConvergenceBrief,
) -> tuple[str, str, str, IntegrationMetrics]:
    """Return the textual panels plus their integration metrics."""

    constellation_panel, nodes, diagnostics = _build_constellation_panel(brief)
    resonance_panel = _build_resonance_panel(brief)
    integration_panel, metrics = _build_integration_panel(brief, nodes, diagnostics)
    return constellation_panel, resonance_panel, integration_panel, metrics


def summarize_convergence(brief: ConvergenceBrief) -> dict[str, object]:
    """Summarize the convergence run with insights and a concise headline."""

    constellation_panel, resonance_panel, integration_panel, metrics = compile_convergence_panels(
        brief
    )
    insights = _derive_integration_insights(metrics, brief)
    headline_parts = [
        f"coverage={metrics.coverage:.3f}",
        f"fusion={metrics.fusion_index:.3f}",
        f"coherence={metrics.coherence:.3f}",
    ]
    if insights.risks:
        headline_parts.append("risks-present")

    return {
        "theme": brief.theme,
        "headline": " | ".join(headline_parts),
        "panels": {
            "constellation": constellation_panel,
            "resonance": resonance_panel,
            "integration": integration_panel,
        },
        "metrics": metrics,
        "insights": insights,
    }


def demo() -> str:
    """Return a demonstration convergence report."""

    brief = ConvergenceBrief(
        theme="signal sanctuary",
        motifs=["aurora lattice", "tidal archive"],
        highlights=["aurora lattice", "community beacon"],
        tone="uplifting",
        energy=1.4,
        constellation_seed=11,
        resonance_seed=21,
    )
    return compose_convergence_report(brief)


def _build_arg_parser() -> "argparse.ArgumentParser":  # pragma: no cover - CLI helper
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("theme", help="Primary theme for the convergence report")
    parser.add_argument(
        "--motif",
        action="append",
        dest="motifs",
        default=None,
        help="Motif to include.  Can be provided multiple times.",
    )
    parser.add_argument(
        "--highlight",
        action="append",
        dest="highlights",
        default=None,
        help="Highlight to include in the resonance panel.",
    )
    parser.add_argument(
        "--tone",
        default="reflective",
        help="Tone to use for the resonance panel (default: reflective)",
    )
    parser.add_argument(
        "--energy",
        type=float,
        default=1.0,
        help="Energy multiplier forwarded to the constellation module.",
    )
    parser.add_argument("--constellation-seed", type=int, default=None)
    parser.add_argument("--resonance-seed", type=int, default=None)
    return parser


def main() -> None:  # pragma: no cover - CLI helper
    parser = _build_arg_parser()
    args = parser.parse_args()
    brief = ConvergenceBrief(
        theme=args.theme,
        motifs=args.motifs or [],
        highlights=args.highlights or [],
        tone=args.tone,
        energy=args.energy,
        constellation_seed=args.constellation_seed,
        resonance_seed=args.resonance_seed,
    )
    print(compose_convergence_report(brief))


if __name__ == "__main__":  # pragma: no cover - CLI helper
    main()
