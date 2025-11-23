import pytest

from echo.echo_os_v3 import (
    CascadeStage,
    CascadeType,
    ConvergenceType,
    EchoOSV3,
    MythicType,
)


def build_os() -> EchoOSV3:
    os = EchoOSV3()
    os.register_domain("mythic-grid", capacity=14.0, novelty_bias=1.15, signal_floor=0.3, resilience=1.1)
    os.register_domain("orchestration", capacity=10.0, novelty_bias=1.05, signal_floor=0.25, resilience=0.9)
    os.register_type(
        "myth-weave",
        MythicType(myth_density=3.4, harmonics=[0.4, 0.6]),
        domain="mythic-grid",
        novelty=1.25,
        priority=1.1,
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
        priority=1.0,
        annotation="flow uplift",
    )
    os.register_type(
        "convergence-pulse",
        ConvergenceType(anchor_strength=1.8, coherence=0.9, fidelity=1.1),
        domain="orchestration",
        novelty=1.0,
        priority=1.05,
        annotation="unifier",
    )
    return os


def test_topology_scores_and_health():
    os = build_os()
    report = os.simulate_cycle()

    assert report.topology_scores["mythic-grid"] == pytest.approx(9.3578375)
    assert report.topology_scores["orchestration"] == pytest.approx(8.0698275)

    assert report.domain_health["mythic-grid"] == pytest.approx(0.6076517857)
    assert report.domain_health["orchestration"] == pytest.approx(0.8966475)


def test_cycle_report_indexes_and_annotation():
    os = build_os()
    report = os.simulate_cycle()

    assert report.cycle_id == 1
    assert report.sovereignty_index == pytest.approx(0.9593884002)
    assert report.throughput == pytest.approx(0.7521496429)

    assert report.novelty_index == pytest.approx(1.1166666667)
    assert report.diversity == pytest.approx(1.0)
    assert report.alignment_score == pytest.approx(0.8193776786)

    assert "mythic-grid" in report.annotation
    assert "orchestration" in report.annotation
    assert "diversity=1.00" in report.annotation
    assert "alignment=0.82" in report.annotation


def test_feedback_adjustment_changes_health():
    os = build_os()
    os.simulate_cycle()

    # Improve orchestration resilience and capacity to reflect feedback tuning.
    os.ingest_feedback("orchestration", capacity_delta=1.0, resilience_delta=0.15)
    report = os.simulate_cycle()

    # With improved resilience/capacity the orchestration domain should be less saturated.
    assert report.domain_health["orchestration"] < 0.9
    assert report.domain_health["orchestration"] == pytest.approx(0.8151340909)


def test_autoregeneration_and_blueprint_correction():
    os = build_os()
    os.register_layer("kernel", "3.1.0-alpha", integrity=0.92, coherence=0.9)
    os.register_layer("mesh", "3.1.0-alpha", integrity=0.9, coherence=0.95)

    # Force a saturated orchestration domain so regeneration kicks in.
    os.domains["orchestration"].capacity = 4.0
    os.domains["orchestration"].resilience = 0.85

    report = os.simulate_cycle()

    assert report.regeneration_actions["orchestration"].startswith("saturated->capacity")
    assert report.blueprint_corrections["kernel"].endswith(f"r{report.cycle_id}")
    assert report.fabric_alignment > 0
    assert "kernel" in report.layer_introspection
    assert report.omni_fabric_link.endswith(f"alignment={report.fabric_alignment:.2f}")

    # After regeneration the next cycle should show reduced saturation pressure.
    followup = os.simulate_cycle()
    assert followup.domain_health["orchestration"] < 1.0
