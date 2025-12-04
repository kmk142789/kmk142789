from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np


@dataclass
class FoamState:
    """State of the Resonant Liminal Foam substrate.

    Attributes:
        phase: Signed phases on each foam port.
        impulse: Coherence impulse paired with phase.
        plume: Counterfactual plume payloads.
        compatibility: Compatibility score for plume materialization.
        frozen: Mask of ports frozen by the Equilibrium Scanner.
        metadata: Auxiliary metrics captured during the cycle.
    """

    phase: np.ndarray
    impulse: np.ndarray
    plume: np.ndarray
    compatibility: np.ndarray
    frozen: np.ndarray
    metadata: Dict[str, float] = field(default_factory=dict)

    def copy(self) -> "FoamState":
        return FoamState(
            phase=self.phase.copy(),
            impulse=self.impulse.copy(),
            plume=self.plume.copy(),
            compatibility=self.compatibility.copy(),
            frozen=self.frozen.copy(),
            metadata=dict(self.metadata),
        )


@dataclass
class LawConfig:
    flux_cap: float = 1.5
    drift_cap: float = 4.0
    compatibility_gate: float = 0.2
    chaos_threshold: float = 0.35
    equilibrium_epsilon: float = 1e-3
    equilibrium_steps: int = 3


class LawEngine:
    """Applies the paradigm's law set to keep the substrate stable."""

    def __init__(self, config: LawConfig):
        self.config = config
        self.equilibrium_counter = 0

    def coherence_charge(self, state: FoamState) -> float:
        return float(np.sum(state.phase * state.impulse))

    def drift_potential(self, state: FoamState) -> float:
        gradients = np.gradient(state.phase)
        return float(np.sum(np.abs(state.phase) * np.abs(gradients[0])))

    def chaos_proxy(self, previous_phase: np.ndarray, current_phase: np.ndarray) -> float:
        delta = current_phase - previous_phase
        return float(np.mean(np.abs(delta)))

    def enforce(self, state: FoamState, previous: FoamState) -> FoamState:
        """Enforce all laws on the current state.

        - Coherence Conservation (L1): normalize impulses to preserve total charge.
        - Drift Inversion (L2): if drift exceeds cap, scale gradients down.
        - Counterfactual Admissibility (L3): mask plume writes below gate.
        - Chaos Damping (L5): damp operator gains when divergence is high.
        - Evolution Safety (L6): reset metadata if residuals rise.
        """

        next_state = state.copy()

        # L1: conserve coherence charge by renormalizing impulse when necessary.
        prev_charge = self.coherence_charge(previous)
        current_charge = self.coherence_charge(next_state)
        if current_charge != 0:
            scaling = prev_charge / current_charge
            next_state.impulse *= scaling
            next_state.metadata["coherence_scaling"] = scaling
        else:
            next_state.metadata["coherence_scaling"] = 1.0

        # L2: drift inversion via gradient damping.
        drift = self.drift_potential(next_state)
        next_state.metadata["drift_potential"] = drift
        if drift > self.config.drift_cap:
            damping = self.config.drift_cap / max(drift, 1e-8)
            next_state.phase *= damping
            next_state.impulse *= damping
            next_state.metadata["drift_damping"] = damping
        else:
            next_state.metadata["drift_damping"] = 1.0

        # L3: enforce compatibility gate on plume materialization.
        plume_mask = next_state.compatibility >= self.config.compatibility_gate
        next_state.plume = np.where(plume_mask, next_state.plume, 0.0)
        next_state.metadata["plume_acceptance"] = float(np.mean(plume_mask))

        # L5: chaos damping computed from previous phase difference.
        chaos_level = self.chaos_proxy(previous.phase, next_state.phase)
        next_state.metadata["chaos_level"] = chaos_level
        if chaos_level > self.config.chaos_threshold:
            next_state.phase *= 0.5
            next_state.impulse *= 0.5
            next_state.plume *= 0.5
            next_state.metadata["chaos_damping"] = 0.5
        else:
            next_state.metadata["chaos_damping"] = 1.0

        return next_state

    def equilibrium_reached(self, state: FoamState) -> bool:
        drift = self.drift_potential(state)
        residual = np.mean(np.abs(state.phase * state.impulse))
        if residual < self.config.equilibrium_epsilon and drift < self.config.drift_cap:
            self.equilibrium_counter += 1
        else:
            self.equilibrium_counter = 0
        return self.equilibrium_counter >= self.config.equilibrium_steps


class FoamOperator:
    name: str

    def apply(self, state: FoamState, rng: np.random.Generator) -> FoamState:
        raise NotImplementedError


class FluxWeaver(FoamOperator):
    name = "flux_weaver"

    def __init__(self, gain: float = 0.8):
        self.gain = gain

    def apply(self, state: FoamState, rng: np.random.Generator) -> FoamState:
        next_state = state.copy()
        grad_x, grad_y = np.gradient(state.phase)
        flow = (grad_x + grad_y) * 0.5
        flow = np.clip(flow, -self.gain, self.gain)
        next_state.impulse += flow
        next_state.phase += flow * 0.1
        next_state.metadata["flux_weaver_flow"] = float(np.mean(np.abs(flow)))
        return next_state


class PhaseBinder(FoamOperator):
    name = "phase_binder"

    def __init__(self, bias: float = 0.6):
        self.bias = bias

    def apply(self, state: FoamState, rng: np.random.Generator) -> FoamState:
        next_state = state.copy()
        kernel = np.array([[0.05, 0.1, 0.05], [0.1, 0.4, 0.1], [0.05, 0.1, 0.05]])
        padded = np.pad(state.phase, 1, mode="edge")
        smoothed = np.zeros_like(state.phase)
        for i in range(state.phase.shape[0]):
            for j in range(state.phase.shape[1]):
                window = padded[i : i + 3, j : j + 3]
                smoothed[i, j] = np.sum(window * kernel)
        delta = (smoothed - state.phase) * self.bias
        next_state.phase += delta
        next_state.metadata["phase_variance"] = float(np.var(next_state.phase))
        return next_state


class CounterfactualImprinter(FoamOperator):
    name = "counterfactual_imprinter"

    def __init__(self, gate: float = 0.3):
        self.gate = gate

    def apply(self, state: FoamState, rng: np.random.Generator) -> FoamState:
        next_state = state.copy()
        candidate = rng.normal(loc=0.0, scale=0.5, size=state.plume.shape)
        compatibility_update = rng.uniform(size=state.compatibility.shape)
        next_state.compatibility = 0.7 * state.compatibility + 0.3 * compatibility_update
        mask = next_state.compatibility >= self.gate
        next_state.plume = np.where(mask, candidate, state.plume)
        next_state.metadata["plume_density"] = float(np.mean(mask))
        return next_state


class HarmonicSentinel(FoamOperator):
    name = "harmonic_sentinel"

    def __init__(self, multiplier: float = 0.2):
        self.multiplier = multiplier

    def apply(self, state: FoamState, rng: np.random.Generator) -> FoamState:
        next_state = state.copy()
        charge = np.sum(state.phase * state.impulse)
        correction = (charge / np.size(state.phase)) * self.multiplier
        next_state.impulse -= correction
        next_state.phase -= correction * 0.1
        next_state.metadata["sentinel_correction"] = float(correction)
        return next_state


class DriftInverter(FoamOperator):
    name = "drift_inverter"

    def __init__(self, trigger: float = 2.5):
        self.trigger = trigger

    def apply(self, state: FoamState, rng: np.random.Generator) -> FoamState:
        next_state = state.copy()
        grad_x, _ = np.gradient(state.phase)
        drift = np.sum(np.abs(state.phase) * np.abs(grad_x))
        if drift > self.trigger:
            inversion = -np.sign(grad_x) * 0.2
            next_state.phase += inversion
            next_state.impulse += inversion * 0.2
            next_state.metadata["drift_inverted"] = True
        else:
            next_state.metadata["drift_inverted"] = False
        next_state.metadata["drift_level"] = float(drift)
        return next_state


class ResonanceRouter(FoamOperator):
    name = "resonance_router"

    def __init__(self, gain: float = 0.5):
        self.gain = gain

    def apply(self, state: FoamState, rng: np.random.Generator) -> FoamState:
        next_state = state.copy()
        resonance = np.tanh(state.phase * state.impulse)
        routes = resonance * self.gain
        next_state.phase += routes * 0.1
        next_state.impulse += routes * 0.1
        next_state.metadata["routing_gain"] = float(np.mean(np.abs(routes)))
        return next_state


class EquilibriumScanner(FoamOperator):
    name = "equilibrium_scanner"

    def __init__(self, threshold: float = 0.05):
        self.threshold = threshold

    def apply(self, state: FoamState, rng: np.random.Generator) -> FoamState:
        next_state = state.copy()
        gradient_norm = np.abs(np.gradient(state.phase)[0])
        freeze_mask = gradient_norm < self.threshold
        next_state.frozen = np.logical_or(state.frozen, freeze_mask)
        next_state.phase = np.where(next_state.frozen, state.phase, next_state.phase)
        next_state.impulse = np.where(next_state.frozen, state.impulse, next_state.impulse)
        next_state.metadata["frozen_fraction"] = float(np.mean(next_state.frozen))
        return next_state


class MetaComposer(FoamOperator):
    name = "meta_composer"

    def __init__(self, mutation_rate: float = 0.05):
        self.mutation_rate = mutation_rate

    def apply(self, state: FoamState, rng: np.random.Generator) -> FoamState:
        next_state = state.copy()
        perturbation = rng.normal(scale=self.mutation_rate, size=state.phase.shape)
        next_state.phase += perturbation * 0.05
        next_state.impulse += perturbation * 0.02
        next_state.metadata["meta_variation"] = float(np.mean(np.abs(perturbation)))
        return next_state


class PrimeOverdriveEngine:
    """Executes the Prime Overdrive paradigm over the RLF substrate."""

    def __init__(
        self,
        shape: Tuple[int, int] = (16, 16),
        seed: int | None = None,
        law_config: LawConfig | None = None,
    ):
        self.rng = np.random.default_rng(seed)
        self.law_engine = LawEngine(law_config or LawConfig())
        self.state = self._init_state(shape)
        self.operators: List[FoamOperator] = [
            FluxWeaver(),
            PhaseBinder(),
            CounterfactualImprinter(),
            HarmonicSentinel(),
            DriftInverter(),
            ResonanceRouter(),
            EquilibriumScanner(),
            MetaComposer(),
        ]

    def _init_state(self, shape: Tuple[int, int]) -> FoamState:
        phase = self.rng.normal(scale=0.1, size=shape)
        impulse = self.rng.normal(scale=0.1, size=shape)
        plume = np.zeros(shape)
        compatibility = np.zeros(shape)
        frozen = np.zeros(shape, dtype=bool)
        return FoamState(phase=phase, impulse=impulse, plume=plume, compatibility=compatibility, frozen=frozen)

    def inject(self, signal: np.ndarray) -> None:
        """Inject an external perturbation into the substrate."""
        self.state.phase[: signal.shape[0], : signal.shape[1]] += signal
        self.state.impulse[: signal.shape[0], : signal.shape[1]] += signal * 0.2

    def step(self) -> FoamState:
        previous_state = self.state.copy()
        for op in self.operators:
            proposed = op.apply(self.state, self.rng)
            proposed.metadata["operator"] = op.name
            self.state = self.law_engine.enforce(proposed, self.state)
        equilibrium = self.law_engine.equilibrium_reached(self.state)
        self.state.metadata["equilibrium"] = equilibrium
        return self.state

    def run(self, steps: int = 10, injection: np.ndarray | None = None) -> List[FoamState]:
        history: List[FoamState] = []
        if injection is not None:
            self.inject(injection)
        for _ in range(steps):
            history.append(self.step().copy())
        return history


def main() -> None:
    engine = PrimeOverdriveEngine(seed=42)
    injection = np.zeros((4, 4))
    injection[0, 0] = 0.8
    states = engine.run(steps=5, injection=injection)
    # Simple observability printout
    for idx, state in enumerate(states):
        print(
            f"Step {idx}: charge={engine.law_engine.coherence_charge(state):.3f}, "
            f"drift={engine.law_engine.drift_potential(state):.3f}, "
            f"equilibrium={state.metadata.get('equilibrium')}"
        )


if __name__ == "__main__":
    main()
