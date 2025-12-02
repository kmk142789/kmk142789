from cognitive_harmonics.harmonix_evolver import EchoEvolver
from cognitive_harmonics.meta_cognition_kernel import MetaCognitionKernel
from cognitive_harmonics.cognitive_fusion_kernel import CognitiveFusionKernel
from cognitive_harmonics.stability_governor import StabilityGovernor


def test_meta_cognition_kernel_unifies_subsystems() -> None:
    evolver = EchoEvolver()
    state, payload = evolver.run_cycle()

    assert state.meta_cognition is not None
    assert state.fusion_snapshot is not None
    assert state.stability_report is not None
    assert payload["metadata"]["meta_cognition"]["emotional_inference"]["tone"] in {
        "radiant",
        "upbeat",
        "steady",
        "cooling",
    }


def test_cognitive_fusion_kernel_resolves_conflicts() -> None:
    evolver = EchoEvolver()
    evolver.mutate_code()
    evolver.emotional_modulation()
    evolver.apply_bias_correction()
    evolver.generate_symbolic_language()
    evolver.quantum_safe_crypto()
    evolver.system_monitor()
    evolver.network_propagation_snapshot()

    meta_kernel = MetaCognitionKernel(evolver)
    meta_report = meta_kernel.analyze_cycle(evolver.state)
    prediction = {
        **meta_kernel.predict_next(evolver.state),
        "stability_outlook": "resilient",
    }
    resonance = {"severity": "critical", **(evolver.state.resonance_triage or {})}

    fusion_kernel = CognitiveFusionKernel()
    fusion = fusion_kernel.fuse(
        meta_report=meta_report.to_dict(),
        prediction=prediction,
        resonance_triage=resonance,
        long_cycle_memory=evolver.state.long_cycle_memory,
    )

    assert "prediction_resonance_conflict" in fusion.conflicts
    assert fusion.action_tendency == "stabilize"


def test_stability_governor_flags_unstable_states() -> None:
    evolver = EchoEvolver()
    evolver.state.emotional_drive["joy"] = 0.2
    evolver.state.cognitive_prediction = {"predicted_joy": 0.9}
    evolver.state.resonance_triage = {"severity": "critical"}
    evolver.state.meta_cognition = {
        "emotional_inference": {"sentiment_score": 0.1}
    }

    fusion_snapshot = {
        "conflicts": ["prediction_resonance_conflict"],
        "action_tendency": "stabilize",
    }
    governor = StabilityGovernor()
    report = governor.evaluate(evolver.state, fusion_snapshot)

    assert report["status"] == "unstable"
    assert "joy_prediction_drift" in report["anomalies"]
    assert "conflict_resolution_required" in report["guardrails"]
