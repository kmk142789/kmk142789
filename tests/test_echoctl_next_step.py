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
