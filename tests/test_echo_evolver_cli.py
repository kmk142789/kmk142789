"""Command line interface tests for :mod:`echo.evolver`."""

from __future__ import annotations

from typing import Dict, List

import pytest

from echo.evolver import main as evolver_main


@pytest.mark.parametrize(
    "argv, expected",
    [
        ([], {"enable_network": False, "persist_artifact": True}),
        (
            ["--enable-network", "--no-persist-artifact"],
            {"enable_network": True, "persist_artifact": False},
        ),
    ],
)
def test_main_parses_runtime_flags(monkeypatch, argv: List[str], expected: Dict[str, bool]) -> None:
    captured: Dict[str, bool] = {}

    class DummyEvolver:
        def run(self, *, enable_network: bool, persist_artifact: bool) -> None:
            captured["enable_network"] = enable_network
            captured["persist_artifact"] = persist_artifact

    monkeypatch.setattr("echo.evolver.EchoEvolver", lambda: DummyEvolver())

    exit_code = evolver_main(argv)

    assert exit_code == 0
    assert captured == expected
