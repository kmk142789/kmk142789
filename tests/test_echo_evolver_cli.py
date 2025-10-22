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


def test_main_supports_continue_evolution(monkeypatch, capsys) -> None:
    captured: Dict[str, object] = {}

    class DummyEvolver:
        amplifier = None

        def continue_evolution(
            self,
            *,
            enable_network: bool,
            persist_artifact: bool,
            include_report: bool,
        ) -> Dict[str, object]:
            captured["kwargs"] = {
                "enable_network": enable_network,
                "persist_artifact": persist_artifact,
                "include_report": include_report,
            }
            return {
                "digest": {
                    "cycle": 3,
                    "progress": 1.0,
                    "remaining_steps": [],
                    "next_step": "Next step: advance_cycle() to begin a new orbit",
                },
                "report": "Cycle 3 Progress\nCompleted: 14/14 (100.0%)\nNext step: advance_cycle() to begin a new orbit",
            }

    monkeypatch.setattr("echo.evolver.EchoEvolver", lambda: DummyEvolver())

    exit_code = evolver_main(["--continue-evolution", "--no-include-report"])

    assert exit_code == 0
    assert captured["kwargs"] == {
        "enable_network": False,
        "persist_artifact": True,
        "include_report": False,
    }

    output = capsys.readouterr().out
    assert "Continued cycle 3" in output
    assert "Cycle 3 Progress" not in output


def test_main_rejects_continue_with_cycles(monkeypatch) -> None:
    class DummyEvolver:
        amplifier = None

    monkeypatch.setattr("echo.evolver.EchoEvolver", lambda: DummyEvolver())

    with pytest.raises(SystemExit) as excinfo:
        evolver_main(["--continue-evolution", "--cycles", "2"])

    assert excinfo.value.code == 2
