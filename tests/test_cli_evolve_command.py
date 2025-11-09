from __future__ import annotations

import json

import pytest

from echo.cli import main


def test_cli_evolve_creates_artifact(tmp_path):
    artifact = tmp_path / "cycle.json"
    code = main(
        [
            "evolve",
            "--seed",
            "7",
            "--artifact",
            str(artifact),
        ]
    )

    assert code == 0
    assert artifact.exists()
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["cycle"] >= 1
    assert payload["emotional_drive"]["joy"] >= 0.0


def test_cli_evolve_requires_positive_cycles():
    with pytest.raises(SystemExit) as exc:
        main(["evolve", "--cycles", "0"])

    assert exc.value.code == 2


def test_cli_evolve_describe_sequence(capfd):
    code = main(["evolve", "--describe-sequence", "--no-persist-artifact"])

    assert code == 0
    captured = capfd.readouterr()
    assert "EchoEvolver cycle sequence" in captured.out
    assert "advance_cycle" in captured.out


def test_cli_evolve_advance_system(monkeypatch, capfd):
    captured = {}

    class DummyEvolver:
        def __init__(self, *args, **kwargs):
            pass

        def advance_system(self, **kwargs):
            captured.update(kwargs)
            return {
                "summary": "Cycle 4 advanced with 14/14 steps complete (100.0% progress).",
                "progress": {"momentum": 1.0},
            }

    monkeypatch.setattr("echo.cli.EchoEvolver", lambda *a, **k: DummyEvolver())

    code = main(
        [
            "evolve",
            "--advance-system",
            "--include-event-summary",
            "--include-propagation",
            "--include-system-report",
            "--include-matrix",
            "--event-summary-limit",
            "7",
            "--system-report-events",
            "9",
            "--no-include-status",
            "--no-include-reflection",
            "--print-artifact",
        ]
    )

    assert code == 0
    assert captured == {
        "enable_network": False,
        "persist_artifact": True,
        "eden88_theme": None,
        "include_manifest": True,
        "include_status": False,
        "include_reflection": False,
        "include_matrix": True,
        "include_event_summary": True,
        "include_propagation": True,
        "include_system_report": True,
        "event_summary_limit": 7,
        "manifest_events": 5,
        "system_report_events": 9,
        "momentum_window": 5,
    }

    output = capfd.readouterr().out
    assert "Cycle 4 advanced" in output
    assert "\"momentum\": 1.0" in output


def test_cli_evolve_manifest_events_require_advance():
    with pytest.raises(SystemExit) as exc:
        main(["evolve", "--manifest-events", "3"])

    assert exc.value.code == 2


def test_cli_evolve_manifest_events_require_manifest():
    with pytest.raises(SystemExit) as exc:
        main(
            [
                "evolve",
                "--advance-system",
                "--no-include-manifest",
                "--manifest-events",
                "2",
            ]
        )

    assert exc.value.code == 2


def test_cli_evolve_momentum_window_requires_advance():
    with pytest.raises(SystemExit) as exc:
        main(["evolve", "--momentum-window", "7"])

    assert exc.value.code == 2


def test_cli_evolve_momentum_window_must_be_positive():
    with pytest.raises(SystemExit) as exc:
        main(["evolve", "--advance-system", "--momentum-window", "0"])

    assert exc.value.code == 2


def test_cli_evolve_custom_momentum_window(monkeypatch):
    captured = {}

    class DummyEvolver:
        def __init__(self, *args, **kwargs):
            pass

        def advance_system(self, **kwargs):
            captured.update(kwargs)
            return {"summary": "Cycle advanced", "progress": {}}

    monkeypatch.setattr("echo.cli.EchoEvolver", lambda *a, **k: DummyEvolver())

    code = main(
        [
            "evolve",
            "--advance-system",
            "--momentum-window",
            "8",
        ]
    )

    assert code == 0
    assert captured["momentum_window"] == 8
