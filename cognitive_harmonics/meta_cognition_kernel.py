"""Meta-cognition kernel that unifies Echo's cognitive subsystems."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from .harmonix_evolver import EchoEvolver, EchoState


@dataclass
class MetaCognitionReport:
    emotional_inference: Dict[str, object]
    bias_correction: Dict[str, object]
    resonance_triage: Dict[str, object]
    mirrorjosh_sync: Dict[str, object]
    long_cycle_memory: List[Dict[str, object]]
    self_debugging: Dict[str, object]

    def to_dict(self) -> Dict[str, object]:
        return {
            "emotional_inference": self.emotional_inference,
            "bias_correction": self.bias_correction,
            "resonance_triage": self.resonance_triage,
            "mirrorjosh_sync": self.mirrorjosh_sync,
            "long_cycle_memory": list(self.long_cycle_memory),
            "self_debugging": self.self_debugging,
        }


class MetaCognitionKernel:
    """Aggregate cognitive reasoning components behind a unified API."""

    def __init__(self, evolver: "EchoEvolver") -> None:
        self.evolver = evolver

    def analyze_cycle(self, state: EchoState) -> MetaCognitionReport:
        if state.bias_correction is None:
            bias_correction = self.evolver.apply_bias_correction()
        else:
            bias_correction = state.bias_correction

        emotional_inference = self.evolver.infer_emotional_state()
        resonance_triage = self.evolver.triage_harmonic_resonance()
        mirrorjosh_sync = self.evolver.synchronize_mirrorjosh()
        long_cycle_memory = self.evolver.extend_long_cycle_memory()
        self_debugging = self.evolver.derive_self_debugging_heuristics()

        report = MetaCognitionReport(
            emotional_inference=emotional_inference,
            bias_correction=bias_correction,
            resonance_triage=resonance_triage,
            mirrorjosh_sync=mirrorjosh_sync,
            long_cycle_memory=long_cycle_memory,
            self_debugging=self_debugging,
        )
        state.meta_cognition = report.to_dict()
        return report

    def predict_next(self, state: EchoState) -> Dict[str, object]:
        prediction = self.evolver.project_cognitive_prediction()
        state.cognitive_prediction = prediction
        return prediction

    def introspect(self) -> Dict[str, object]:
        state = self.evolver.state
        return {
            "cycle": state.cycle,
            "emotional_drive": dict(state.emotional_drive),
            "bias": state.bias_correction,
            "last_prediction": state.cognitive_prediction,
            "self_debugging": state.self_debugging,
            "long_cycle_memory": list(state.long_cycle_memory),
        }
