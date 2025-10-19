"""Behavioural tests for :meth:`echo.evolver.EchoEvolver.generate_symbolic_language`."""

from __future__ import annotations

import pytest

from echo.evolver import EchoEvolver


@pytest.fixture()
def evolver() -> EchoEvolver:
    return EchoEvolver()


def test_generate_symbolic_language_ignores_unknown_glyphs(monkeypatch, evolver: EchoEvolver) -> None:
    evolver.state.cycle = 0
    sequence = "∇?≋!"
    monkeypatch.setattr(evolver, "_symbolic_sequence", lambda: sequence)

    result = evolver.generate_symbolic_language()

    assert result == sequence
    assert evolver.state.network_cache["oam_vortex"] == "0000000000000101"
    assert evolver.state.glyphs.endswith("≋∇")
