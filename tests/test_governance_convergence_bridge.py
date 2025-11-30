from src.creative_convergence import ConvergenceBrief
from src.governance_convergence_bridge import (
    coordinate_multi_agent_convergence,
    fuse_portfolio_with_governance,
    stream_real_time_insights,
)


def _brief(theme: str, highlights: list[str]) -> ConvergenceBrief:
    return ConvergenceBrief(
        theme=theme,
        motifs=["anchor", "coherence"],
        highlights=highlights,
        tone="assured",
        energy=1.1,
        constellation_seed=len(theme),
        resonance_seed=len(highlights),
    )


def test_fusion_identifies_blindspots_and_trust_gaps() -> None:
    briefs = [
        _brief("convergence", ["coverage", "trust"]),
        _brief("governance", ["trust", "policy"]),
    ]
    snapshot = {"stable": ["telemetry"], "escalate": ["governance"], "policy": {"governance": "stabilize"}}

    fusion = fuse_portfolio_with_governance(briefs, snapshot)

    assert fusion.blindspots, "should surface lexical blindspots from portfolio"
    assert fusion.trust_gaps, "should surface governance trust gaps"
    assert 0.0 <= fusion.policy_alignment <= 1.0


def test_stream_surfaces_real_time_events() -> None:
    fusion = fuse_portfolio_with_governance(
        [_brief("creative", ["idea", "clarity"]), _brief("signal", ["clarity", "orbit"])],
        {"stable": ["analytics"], "escalate": [], "policy": {}},
    )

    events = stream_real_time_insights(fusion)
    kinds = {event["type"] for event in events}

    assert "dashboard" in kinds
    assert "creative_burst" in kinds


def test_multi_agent_convergence_generates_gap_briefs() -> None:
    briefs = [
        _brief("atlas", ["navigation", "map"]),
        _brief("ledger", ["integrity", "audit"]),
    ]
    follow_ups = coordinate_multi_agent_convergence(briefs)

    assert follow_ups, "should propose collaborative briefs to close gaps"
    assert all(brief.tone == "collaborative" for brief in follow_ups)
