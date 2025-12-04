"""Cognitive Equilibrium Regulator (CER).

This module stabilizes cognitive dynamics predicted by CFIE by applying
corrective vectors back into the manifold. It mirrors a control-system
loop that dampens overload and collapse risks in near real time.
"""
from __future__ import annotations

from typing import Mapping, Optional

import numpy as np

from .cognitive_field_inference_engine import CFIEngine


class CognitiveEquilibriumRegulator:
    """Stabilizes cognitive dynamics predicted by CFIE."""

    def __init__(
        self,
        gain: float = 0.05,
        damping: float = 0.1,
        random_state: Optional[np.random.Generator] = None,
    ) -> None:
        self.gain = float(gain)
        self.damping = float(damping)
        self.rng = random_state or np.random.default_rng()

    def compute_intervention(self, forecast: Mapping[str, object], manifold_state: np.ndarray) -> np.ndarray:
        """Calculate a stabilizing vector based on cognitive instability."""

        overload = bool(forecast.get("overload_risk", False))
        collapse = bool(forecast.get("attentional_collapse", False))
        instability = float(forecast.get("instability_index", 0.0))

        corrective = np.zeros_like(manifold_state)

        if overload:
            corrective -= self.gain * np.abs(manifold_state)

        if collapse:
            corrective += self.gain * self.rng.uniform(-1.0, 1.0, size=manifold_state.shape)

        gradient = np.gradient(manifold_state) if manifold_state.size else np.array([])
        corrective -= self.damping * np.array(gradient)
        corrective -= 0.5 * self.damping * instability * np.sign(manifold_state)

        return corrective

    def apply(self, cfie_engine: CFIEngine) -> np.ndarray:
        """Reads cognitive state → computes correction → injects back."""

        if cfie_engine.last_forecast is None:
            raise ValueError("CFIEngine has not produced a forecast yet.")

        correction = self.compute_intervention(cfie_engine.last_forecast, cfie_engine.manifold.state)
        cfie_engine.manifold.update(correction)

        return correction

