import pytest

from echo.echo_os_v2 import (
    CascadeStage,
    CascadeType,
    ConvergenceType,
    EchoOSV2,
    MythicType,
)


def build_os() -> EchoOSV2:
    os = EchoOSV2()
    os.register_domain("mythic-grid", capacity=14.0, novelty_bias=1.15, signal_floor=0.3)
    os.register_domain("orchestration", capacity=10.0, novelty_bias=1.05, signal_floor=0.25)
    os.register_type(
        "myth-weave",
        MythicType(myth_density=3.4, harmonics=[0.4, 0.6]),
        domain="mythic-grid",
        novelty=1.25,
        annotation="story kernel",
    )
    os.register_type(
        "cascade-lattice",
        CascadeType(
            base_flow=2.0,
            stages=[CascadeStage(gain=1.2, drag=0.1), CascadeStage(gain=0.8, drag=0.2)],
            fidelity=0.8,
        ),
        domain="orchestration",
        novelty=1.1,
        annotation="flow uplift",
    )
    os.register_type(
        "convergence-pulse",
        ConvergenceType(anchor_strength=1.8, coherence=0.9, fidelity=1.1),
        domain="orchestration",
        novelty=1.0,
        annotation="unifier",
    )
    return os


def test_topology_scores_and_health():
    os = build_os()
    report = os.simulate_cycle()

    assert report.topology_scores["mythic-grid"] == pytest.approx(7.73375)
    assert report.topology_scores["orchestration"] == pytest.approx(8.71605)

    assert report.domain_health["mythic-grid"] == pytest.approx(0.55241071428)
    assert report.domain_health["orchestration"] == pytest.approx(0.871605)


def test_cycle_report_manifest_and_index():
    os = build_os()
    report = os.simulate_cycle()

    assert report.cycle_id == 1
    assert report.sovereignty_index == pytest.approx(0.9778241238)
    assert report.throughput == pytest.approx(0.71200785714)

    assert "myth-weave" in report.type_manifest
    assert "cascade-lattice" in report.type_manifest
    assert "convergence-pulse" in report.type_manifest

    assert "mythic-grid" in report.annotation
    assert "orchestration" in report.annotation
