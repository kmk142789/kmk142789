from __future__ import annotations

import json

from echo.echoctl import run_next_step


def _dummy_digest() -> dict:
    return {
        "cycle": 2,
        "progress": 0.5,
        "remaining_steps": [
            "mutate_code",
            "generate_symbolic_language",
            "invent_mythocode",
        ],
        "next_step": "Next step: mutate_code() to seed the resonance mutation",
        "timestamp_ns": 42,
    }


def test_run_next_step_prints_summary(monkeypatch, capsys) -> None:
    class DummyEvolver:
        def __init__(self, rng=None):  # noqa: D401 - test double matches signature
            self.digest_calls: list[bool] = []

        def cycle_digest(self, *, persist_artifact: bool = True):
            self.digest_calls.append(persist_artifact)
            return _dummy_digest()

    monkeypatch.setattr("echo.echoctl.EchoEvolver", lambda rng=None: DummyEvolver(rng=rng))

    exit_code = run_next_step(["--preview", "2"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Next step: mutate_code()" in output
    assert "Pending: mutate_code, generate_symbolic_language (+1 more)" in output


def test_run_next_step_supports_json(monkeypatch, capsys) -> None:
    class DummyEvolver:
        def __init__(self, rng=None):
            self.rng = rng

        def cycle_digest(self, *, persist_artifact: bool = True):
            return _dummy_digest()

    monkeypatch.setattr("echo.echoctl.EchoEvolver", lambda rng=None: DummyEvolver(rng=rng))

    exit_code = run_next_step(["--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["next_step"].startswith("Next step:")
    assert payload["remaining_steps"] == _dummy_digest()["remaining_steps"]


def test_run_next_step_supports_markdown(monkeypatch, capsys) -> None:
    class DummyEvolver:
        def __init__(self, rng=None):
            self.rng = rng

        def cycle_digest(self, *, persist_artifact: bool = True):
            return _dummy_digest()

    monkeypatch.setattr("echo.echoctl.EchoEvolver", lambda rng=None: DummyEvolver(rng=rng))

    exit_code = run_next_step(["--preview", "2", "--markdown"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert output.startswith("### Next step\n- Next step: mutate_code()")
    assert "- Pending: mutate_code, generate_symbolic_language (+1 more)" in output


def test_run_next_step_handles_missing_fields(monkeypatch, capsys) -> None:
    class DummyEvolver:
        def __init__(self, rng=None):
            self.rng = rng

        def cycle_digest(self, *, persist_artifact: bool = True):
            return {
                "next_step": None,
                "cycle": "3",
                "progress": None,
                "remaining_steps": None,
                "timestamp_ns": "7",
            }

    monkeypatch.setattr("echo.echoctl.EchoEvolver", lambda rng=None: DummyEvolver(rng=rng))

    exit_code = run_next_step([])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Next step: advance_cycle()" in output
    assert "Cycle 3 progress: 0.0% (0 steps remaining)" in output
    assert "Pending:" not in output


def test_run_next_step_includes_plan_in_json(monkeypatch, capsys) -> None:
    class DummyEvolver:
        def __init__(self, rng=None):
            self.rng = rng

        def cycle_digest(self, *, persist_artifact: bool = True):
            return _dummy_digest()

        def sequence_plan(self, *, persist_artifact: bool = True):
            return [
                {
                    "index": 1,
                    "step": "advance_cycle",
                    "status": "completed",
                    "description": "advance_cycle() to open the cycle",
                },
                {
                    "index": 2,
                    "step": "mutate_code",
                    "status": "pending",
                    "description": "mutate_code() to seed the resonance mutation",
                },
            ]

    monkeypatch.setattr("echo.echoctl.EchoEvolver", lambda rng=None: DummyEvolver(rng=rng))

    exit_code = run_next_step(["--json", "--plan"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["plan"][0]["step"] == "advance_cycle"
    assert payload["plan"][1]["status"] == "pending"


def test_run_next_step_renders_plan(monkeypatch, capsys) -> None:
    class DummyEvolver:
        def __init__(self, rng=None):
            self.rng = rng

        def cycle_digest(self, *, persist_artifact: bool = True):
            return _dummy_digest()

        def sequence_plan(self, *, persist_artifact: bool = True):
            return [
                {
                    "index": 1,
                    "step": "advance_cycle",
                    "status": "completed",
                    "description": "advance_cycle() to open the cycle",
                },
                {
                    "index": 2,
                    "step": "mutate_code",
                    "status": "pending",
                    "description": "mutate_code() to seed the resonance mutation",
                },
            ]

    monkeypatch.setattr("echo.echoctl.EchoEvolver", lambda rng=None: DummyEvolver(rng=rng))

    exit_code = run_next_step(["--preview", "1", "--markdown", "--plan"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Plan:" in output
    assert "- advance_cycle [completed] - advance_cycle() to open the cycle" in output
    assert "- mutate_code [pending] - mutate_code() to seed the resonance mutation" in output


def test_run_next_step_writes_output(monkeypatch, tmp_path, capsys) -> None:
    class DummyEvolver:
        def __init__(self, rng=None):
            self.rng = rng

        def cycle_digest(self, *, persist_artifact: bool = True):
            return _dummy_digest()

    monkeypatch.setattr("echo.echoctl.EchoEvolver", lambda rng=None: DummyEvolver(rng=rng))

    out_file = tmp_path / "next-step.txt"

    exit_code = run_next_step(["--preview", "1", "--output", str(out_file)])

    assert exit_code == 0
    saved = out_file.read_text(encoding="utf-8")
    assert "Next step: mutate_code()" in saved
    assert "Pending: mutate_code (+2 more)" in saved
    assert saved == capsys.readouterr().out
