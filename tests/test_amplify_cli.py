from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from echo import cli
from echo.amplify import AmplificationEngine


@pytest.fixture(autouse=True)
def deterministic_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    original_init = AmplificationEngine.__init__

    def _patched_init(self, *args, **kwargs):  # type: ignore[override]
        original_init(self, *args, **kwargs)
        self.time_source = lambda: datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
        self.commit_source = lambda: "deadbeef"

    monkeypatch.setattr(cli, "AmplificationEngine", AmplificationEngine)
    monkeypatch.setattr(AmplificationEngine, "__init__", _patched_init)


@pytest.fixture()
def manifest(tmp_path: Path) -> Path:
    data = {
        "evolver": {
            "cycle": 4,
            "emotional_drive": {"joy": 0.9, "curiosity": 0.85, "rage": 0.15},
            "propagation_channels": 5,
            "network_nodes": 11,
            "orbital_hops": 4,
        },
        "mythocode": ["a", "b", "c"],
        "events": ["one", "two"],
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.fixture()
def log_path(tmp_path: Path) -> Path:
    return tmp_path / "amplify.jsonl"


def test_amplify_now_is_idempotent(manifest: Path, log_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(
        [
            "amplify",
            "now",
            "--manifest",
            str(manifest),
            "--log-path",
            str(log_path),
        ]
    )
    assert exit_code == 0
    first = capsys.readouterr().out

    second_code = cli.main(
        [
            "amplify",
            "now",
            "--manifest",
            str(manifest),
            "--log-path",
            str(log_path),
        ]
    )
    assert second_code == 0
    second = capsys.readouterr().out
    assert first == second

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1


def test_amplify_log_and_gate(monkeypatch: pytest.MonkeyPatch, manifest: Path, log_path: Path) -> None:
    cli.main([
        "amplify",
        "now",
        "--manifest",
        str(manifest),
        "--log-path",
        str(log_path),
    ])

    assert cli.main([
        "amplify",
        "log",
        "--manifest",
        str(manifest),
        "--log-path",
        str(log_path),
        "--limit",
        "2",
    ]) == 0

    assert (
        cli.main(
            [
                "amplify",
                "gate",
                "--manifest",
                str(manifest),
                "--log-path",
                str(log_path),
                "--min",
                "99",
            ]
        )
        == 1
    )


def test_forecast_cli(manifest: Path, log_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cli.main([
        "amplify",
        "now",
        "--manifest",
        str(manifest),
        "--log-path",
        str(log_path),
    ])
    exit_code = cli.main(
        [
            "forecast",
            "--manifest",
            str(manifest),
            "--log-path",
            str(log_path),
            "--cycles",
            "12",
            "--plot",
        ]
    )
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Baseline" in output
    assert "sparkline" in output
