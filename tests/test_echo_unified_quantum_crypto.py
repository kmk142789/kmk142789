from __future__ import annotations

from typing import List, Tuple

from echo_unified_all import EchoEvolver


class RiggedEvolver(EchoEvolver):
    """Evolver with deterministic entropy and drift analysis for tests."""

    def __init__(
        self,
        *,
        entropy: bytes,
        drift_result: Tuple[float, int],
        seed: int | None = None,
    ) -> None:
        super().__init__(seed=seed)
        self._test_entropy = entropy
        self._drift_result = drift_result

    def _entropy_seed(self) -> bytes:
        return self._test_entropy

    def _drift_analysis(self, numeric_history: List[int]) -> Tuple[float, int]:
        # Ignore ``numeric_history`` because the tests provide an explicit result.
        return self._drift_result


def test_quantum_safe_crypto_discards_key_on_drift() -> None:
    evolver = RiggedEvolver(entropy=b"\x01" * 48, drift_result=(0.9, 1234), seed=7)
    evolver.state.cycle = 4
    evolver.state.vault_key = "existing"
    evolver._rng.random = lambda: 0.0  # Always use fresh entropy path.

    key = evolver.quantum_safe_crypto()

    assert key is None
    assert evolver.state.vault_key is None
    assert evolver.state.vault_key_status["status"] == "discarded"
    assert evolver.state.vault_key_status["relative_delta"] == 0.9
    assert evolver.state.event_log[-1].startswith("Quantum key discarded")


def test_quantum_safe_crypto_returns_hybrid_key_when_stable() -> None:
    evolver = RiggedEvolver(entropy=b"\x02" * 48, drift_result=(0.1, 987654), seed=11)
    evolver.state.cycle = 3
    evolver._rng.random = lambda: 0.0

    key = evolver.quantum_safe_crypto()

    assert key is not None
    assert key.startswith("SAT-TF-QKD:∇")
    assert f"|ORBIT:{evolver.state.system_metrics.orbital_hops}" in key
    assert evolver.state.vault_key == key
    status = evolver.state.vault_key_status
    assert status["status"] == "active"
    assert status["key"] == key
    assert status["relative_delta"] == 0.1
    assert evolver.state.event_log[-1] == "Quantum key refreshed"
