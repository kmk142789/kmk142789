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


def test_generate_symbolic_language_runs_registered_hooks(monkeypatch, evolver: EchoEvolver) -> None:
    calls: list[str] = []

    def base_action() -> None:
        calls.append("base")

    def hook_one() -> None:
        calls.append("hook_one")

    def hook_two() -> None:
        calls.append("hook_two")

    monkeypatch.setattr(evolver, "_symbolic_sequence", lambda: "∇∇")
    monkeypatch.setattr(evolver, "_symbolic_actions", lambda: {"∇": (base_action,)})

    evolver.register_symbolic_action("∇", hook_one)
    evolver.register_symbolic_action("∇", hook_two)

    result = evolver.generate_symbolic_language()

    assert result == "∇∇"
    assert calls.count("base") == 2
    assert calls.count("hook_one") == 2
    assert calls.count("hook_two") == 2
