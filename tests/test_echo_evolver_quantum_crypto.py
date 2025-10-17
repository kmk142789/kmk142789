"""Tests covering the evolver's quantum safe crypto drift handling."""

from __future__ import annotations

from typing import Callable

from echo.evolver import EchoEvolver


class RiggedEvolver(EchoEvolver):
    """Evolver with deterministic entropy for unit tests."""

    def __init__(self, *, entropy: bytes, **kwargs) -> None:
        super().__init__(**kwargs)
        self._test_entropy = entropy

    def _entropy_seed(self) -> bytes:
        return self._test_entropy


def _rigged_random(value: float) -> Callable[[], float]:
    return lambda: value


def test_quantum_safe_crypto_records_drift_discard() -> None:
    entropy = bytes.fromhex("8795d2168bc1f4b5")
    evolver = RiggedEvolver(entropy=entropy)
    evolver.state.cycle = 5
    evolver.state.vault_key = "existing-key"
    evolver.rng.random = _rigged_random(0.0)

    key = evolver.quantum_safe_crypto()

    assert key is None
    assert evolver.state.vault_key is None

    assert evolver.state.event_log[-1].startswith("Quantum key discarded: drift Δ=")

    status = evolver.state.network_cache["vault_key_status"]
    assert status["status"] == "discarded"
    assert status["relative_delta"] > 0.75
    assert "key" not in status

    completed = evolver.state.network_cache["completed_steps"]
    assert "quantum_safe_crypto" in completed

