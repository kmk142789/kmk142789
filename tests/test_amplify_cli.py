from __future__ import annotations

from dataclasses import dataclass

import pytest

from echo.amplify import AmplificationMetrics, AmplifyRecord
from echo.manifest_cli import main as cli_main


@dataclass
class StubEngine:
    record: AmplifyRecord
    history: list[AmplifyRecord]
    gate_result: tuple[bool, float | None]

    def measure_and_record(self, *_args, **_kwargs) -> AmplifyRecord:
        return self.record

    def tail(self, count: int) -> list[AmplifyRecord]:
        return self.history[-count:]

    def sparkline(self, count: int = 8) -> str:
        return "▇" * len(self.tail(count))

    def ensure_gate(self, _minimum: float | None = None) -> tuple[bool, float | None]:
        return self.gate_result


def _make_metrics(index: float) -> AmplificationMetrics:
    return AmplificationMetrics(
        resonance=index,
        freshness_half_life=index,
        novelty_delta=index,
        cohesion=index,
        coverage=index,
        volatility=index,
        index=index,
    )


def _make_record(index: float, *, timestamp: float = 100.0, cycle: int | None = None) -> AmplifyRecord:
    return AmplifyRecord(timestamp=timestamp, metrics=_make_metrics(index), cycle=cycle)


def test_amplify_now_command(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    record = _make_record(75.5, cycle=5)
    engine = StubEngine(record=record, history=[record], gate_result=(True, 75.5))
    monkeypatch.setattr("echo.manifest_cli.AmplifyEngine", lambda: engine)

    exit_code = cli_main(["amplify", "now"])
    assert exit_code == 0

    output = capsys.readouterr().out
    assert "Amplify Index: 75.50" in output
    assert '"index": 75.5' in output
    assert "Sparkline" in output


def test_amplify_log_command(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    history = [
        _make_record(60.0, timestamp=10.0, cycle=1),
        _make_record(82.0, timestamp=20.0, cycle=2),
    ]
    engine = StubEngine(record=history[-1], history=history, gate_result=(True, 82.0))
    monkeypatch.setattr("echo.manifest_cli.AmplifyEngine", lambda: engine)

    exit_code = cli_main(["amplify", "log", "--count", "2"])
    assert exit_code == 0

    output = capsys.readouterr().out
    assert "cycle 1" in output
    assert '"index": 82.0' in output
    assert "Sparkline:" in output


def test_amplify_gate_failure(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    record = _make_record(65.0, cycle=3)
    engine = StubEngine(record=record, history=[record], gate_result=(False, 65.0))
    monkeypatch.setattr("echo.manifest_cli.AmplifyEngine", lambda: engine)

    exit_code = cli_main(["amplify", "gate", "--min", "70"])
    assert exit_code == 1

    output = capsys.readouterr().out
    assert "❌ Amplify gate failed" in output
