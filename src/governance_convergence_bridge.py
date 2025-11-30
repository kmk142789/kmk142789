"""Bridge creative convergence insights into governance intelligence.

This module fuses the convergence portfolio with governance signals so the
system can self-audit creative blindspots and trust gaps.  It also provides
lightweight real-time streaming utilities to surface dashboards, alerts, and
collaborative "creative bursts" across cooperating agents.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Mapping, Sequence

from .creative_convergence import ConvergenceBrief
from .creative_convergence_portfolio import PortfolioDigest, build_portfolio_digest


@dataclass(frozen=True)
class CreativeBlindspot:
    """Represents a missing or under-served idea in the portfolio."""

    phrase: str
    occurrences: int
    affected_themes: tuple[str, ...]


@dataclass(frozen=True)
class GovernanceTrustGap:
    """Captures where governance signals report weakening trust."""

    focus: str
    severity: float
    rationale: str


@dataclass(frozen=True)
class FusionInsight:
    """Composite view combining portfolio and governance signals."""

    portfolio: PortfolioDigest
    blindspots: tuple[CreativeBlindspot, ...]
    trust_gaps: tuple[GovernanceTrustGap, ...]
    policy_alignment: float
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def fuse_portfolio_with_governance(
    briefs: Iterable[ConvergenceBrief],
    governance_snapshot: Mapping[str, object] | None = None,
) -> FusionInsight:
    """Fuse convergence and governance signals into a single insight.

    ``governance_snapshot`` mirrors the shape produced by the governance probe
    inside :class:`packages.core.echo.echo_genesis_core.EchoGenesisCore`.
    Unknown or missing governance data is handled gracefully so the fusion can
    operate in offline test environments.
    """

    snapshot = dict(governance_snapshot or {})
    digest = build_portfolio_digest(briefs)

    blindspots = _collect_blindspots(digest)
    trust_gaps = _collect_trust_gaps(snapshot)

    stable = snapshot.get("stable") or []
    escalate = snapshot.get("escalate") or []
    total_tracks = len(stable) + len(escalate)
    stability_ratio = len(stable) / total_tracks if total_tracks else 0.5

    # Portfolio alignment anchors governance trust; gaps drag it down.
    gap_penalty = 0.05 * len(blindspots)
    alignment_score = max(0.0, min(1.0, digest.average_alignment * stability_ratio - gap_penalty))

    return FusionInsight(
        portfolio=digest,
        blindspots=tuple(blindspots),
        trust_gaps=tuple(trust_gaps),
        policy_alignment=round(alignment_score, 3),
    )


def stream_real_time_insights(
    fusion: FusionInsight, *, include_alerts: bool = True
) -> list[Mapping[str, object]]:
    """Render a small batch of real-time dashboard events.

    The stream is intentionally lightweight and structured so it can be
    forwarded to websockets, SSE, or in-memory subscribers without requiring an
    additional runtime dependency.
    """

    events: list[Mapping[str, object]] = [
        {
            "type": "dashboard",
            "generated_at": fusion.timestamp,
            "portfolio": {
                "entries": len(fusion.portfolio.entries),
                "alignment": fusion.portfolio.average_alignment,
                "consistency": fusion.portfolio.consistency_index,
            },
        }
    ]

    if include_alerts:
        for blindspot in fusion.blindspots:
            events.append(
                {
                    "type": "alert",
                    "level": "anomaly" if blindspot.occurrences > 1 else "notice",
                    "message": f"Blindspot: '{blindspot.phrase}' missing across {blindspot.occurrences} briefs",
                    "affected_themes": blindspot.affected_themes,
                }
            )
        for gap in fusion.trust_gaps:
            events.append(
                {
                    "type": "alert",
                    "level": "governance",
                    "message": f"Trust gap detected on {gap.focus}",
                    "severity": gap.severity,
                    "rationale": gap.rationale,
                }
            )

    # Creative bursts encourage agents to swarm around gaps.
    if fusion.blindspots:
        events.append(
            {
                "type": "creative_burst",
                "targets": [spot.phrase for spot in fusion.blindspots][:3],
                "alignment": fusion.policy_alignment,
            }
        )

    return events


def coordinate_multi_agent_convergence(
    briefs: Sequence[ConvergenceBrief],
    *,
    fill_energy: float = 0.9,
) -> tuple[ConvergenceBrief, ...]:
    """Propose follow-up briefs where agents automatically fill each other's gaps."""

    digest = build_portfolio_digest(briefs)
    gap_targets = [phrase for phrase, count in digest.gap_hotspots if count > 0]
    if not gap_targets:
        return ()

    collaborative_briefs: list[ConvergenceBrief] = []
    for index, target in enumerate(gap_targets):
        # Pair each gap with the strongest coverage leader to amplify closure.
        motifs = {digest.coverage_leader.theme, target}
        highlights = {target, digest.intensity_leader.theme}
        collaborative_briefs.append(
            ConvergenceBrief(
                theme=f"gap-bridge-{index+1}:{target}",
                motifs=tuple(motifs),
                highlights=tuple(highlights),
                tone="collaborative",
                energy=fill_energy,
                constellation_seed=100 + index,
                resonance_seed=200 + index,
            )
        )
    return tuple(collaborative_briefs)


def _collect_blindspots(digest: PortfolioDigest) -> list[CreativeBlindspot]:
    blindspots: list[CreativeBlindspot] = []
    for phrase, count in digest.gap_hotspots:
        affected = tuple(
            entry.theme for entry in digest.entries if phrase in entry.metrics.lexical_gaps
        )
        blindspots.append(CreativeBlindspot(phrase=phrase, occurrences=count, affected_themes=affected))
    return blindspots


def _collect_trust_gaps(snapshot: Mapping[str, object]) -> list[GovernanceTrustGap]:
    trust_gaps: list[GovernanceTrustGap] = []
    escalations = snapshot.get("escalate") or []
    policies = snapshot.get("policy") or {}

    for name in escalations:
        rationale = policies.get(name) if isinstance(policies, Mapping) else None
        trust_gaps.append(
            GovernanceTrustGap(
                focus=name,
                severity=0.7 if len(escalations) > 1 else 0.5,
                rationale=str(rationale or "stabilize focus"),
            )
        )
    return trust_gaps


__all__ = [
    "CreativeBlindspot",
    "GovernanceTrustGap",
    "FusionInsight",
    "fuse_portfolio_with_governance",
    "stream_real_time_insights",
    "coordinate_multi_agent_convergence",
]
