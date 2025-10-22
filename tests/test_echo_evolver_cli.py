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
            include_status: bool,
        ) -> Dict[str, object]:
            captured["kwargs"] = {
                "enable_network": enable_network,
                "persist_artifact": persist_artifact,
                "include_report": include_report,
                "include_status": include_status,
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
        "include_status": True,
    }

    output = capsys.readouterr().out
    assert "Continued cycle 3" in output
    assert "Cycle 3 Progress" not in output


def test_main_allows_disabling_status_snapshot(monkeypatch) -> None:
    captured: Dict[str, object] = {}

    class DummyEvolver:
        amplifier = None

        def continue_evolution(
            self,
            *,
            enable_network: bool,
            persist_artifact: bool,
            include_report: bool,
            include_status: bool,
        ) -> Dict[str, object]:
            captured["kwargs"] = {
                "enable_network": enable_network,
                "persist_artifact": persist_artifact,
                "include_report": include_report,
                "include_status": include_status,
            }
            return {
                "digest": {
                    "cycle": 1,
                    "progress": 1.0,
                    "remaining_steps": [],
                    "next_step": "Next step: advance_cycle() to begin a new orbit",
                }
            }

    monkeypatch.setattr("echo.evolver.EchoEvolver", lambda: DummyEvolver())

    exit_code = evolver_main(["--continue-evolution", "--no-include-status"])

    assert exit_code == 0
    assert captured["kwargs"] == {
        "enable_network": False,
        "persist_artifact": True,
        "include_report": True,
        "include_status": False,
    }


def test_main_rejects_continue_with_cycles(monkeypatch) -> None:
    class DummyEvolver:
        amplifier = None

    monkeypatch.setattr("echo.evolver.EchoEvolver", lambda: DummyEvolver())

    with pytest.raises(SystemExit) as excinfo:
        evolver_main(["--continue-evolution", "--cycles", "2"])

    assert excinfo.value.code == 2


def test_main_supports_advance_system(monkeypatch, capsys) -> None:
    captured = {}

    class DummyEvolver:
        amplifier = None

        def advance_system(
            self,
            *,
            enable_network: bool,
            persist_artifact: bool,
            eden88_theme: str | None,
            include_manifest: bool,
            include_status: bool,
            include_reflection: bool,
        ) -> dict[str, object]:
            captured["kwargs"] = {
                "enable_network": enable_network,
                "persist_artifact": persist_artifact,
                "eden88_theme": eden88_theme,
                "include_manifest": include_manifest,
                "include_status": include_status,
                "include_reflection": include_reflection,
            }
            return {
                "summary": "Cycle 4 advanced with 14/14 steps complete (100.0% progress).",
                "report": "Cycle 4 Progress\nCompleted: 14/14 (100.0%)\nNext step: advance_cycle() to begin a new orbit",
                "digest": {"cycle": 4, "progress": 1.0, "steps": []},
                "status": {"cycle": 4, "progress": 1.0},
            }

    monkeypatch.setattr("echo.evolver.EchoEvolver", lambda: DummyEvolver())

    exit_code = evolver_main([
        "--advance-system",
        "--enable-network",
        "--no-include-status",
        "--eden88-theme",
        "aurora",
    ])

    assert exit_code == 0
    assert captured["kwargs"] == {
        "enable_network": True,
        "persist_artifact": True,
        "eden88_theme": "aurora",
        "include_manifest": True,
        "include_status": False,
        "include_reflection": True,
    }

    output = capsys.readouterr().out
    assert "Cycle 4 advanced" in output
    assert "Cycle 4 Progress" in output
