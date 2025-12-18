"""Tests for :mod:`src.convergence_trajectory`."""

from src.convergence_trajectory import build_convergence_trajectory
from src.creative_convergence import ConvergenceBrief


def _brief(theme: str, motifs: list[str], highlights: list[str], *, seed: int) -> ConvergenceBrief:
    return ConvergenceBrief(
        theme=theme,
        motifs=motifs,
        highlights=highlights,
        tone="uplifting",
        energy=1.1,
        constellation_seed=seed,
        resonance_seed=seed + 5,
    )


def test_trajectory_tracks_trends_and_readiness_counts() -> None:
    phases = [
        ("alpha", _brief("signal sanctuary", ["signal", "sanctuary"], ["signal"], seed=3)),
        ("beta", _brief("signal sanctuary", ["signal"], ["signal", "bridge"], seed=4)),
        ("gamma", _brief("signal sanctuary", ["signal", "bridge"], ["signal", "bridge"], seed=5)),
    ]

    trajectory = build_convergence_trajectory(phases)

    assert trajectory.coverage_trend[0] <= trajectory.coverage_trend[-1]
    assert trajectory.fusion_trend[0] <= trajectory.fusion_trend[-1]
    assert trajectory.coherence_trend[0] <= trajectory.coherence_trend[-1]
    assert sum(trajectory.readiness_counts.values()) == len(phases)
    assert trajectory.momentum >= 0
    assert len(trajectory.stability_corridor) == 3
    rendered = trajectory.render()
    assert "Convergence Trajectory" in rendered
    assert "readiness" in rendered


def test_trajectory_flags_anomalies_when_alignment_drops() -> None:
    phases = [
        ("baseline", _brief("lexical lattice", ["lexical"], ["lexical"], seed=11)),
        ("regression", _brief("lexical lattice", ["grid"], ["lexical"], seed=12)),
    ]

    trajectory = build_convergence_trajectory(phases)

    assert trajectory.anomaly_flags
    assert any("coverage drop" in flag for flag in trajectory.anomaly_flags)
