import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from echo.amplify import AmplificationEngine
from echo.manifest_cli import main as echo_main


def _state(cycle: int) -> dict:
    return {
        "cycle": cycle,
        "mythocode": [f"cycle::{cycle}", f"glyph::{cycle * 7}"],
        "event_log": [f"event-{cycle}-{idx}" for idx in range(5)],
        "emotional_drive": {"joy": 0.9, "curiosity": 0.87, "rage": 0.12},
        "network_cache": {
            "completed_steps": {
                "advance_cycle",
                "mutate_code",
                "emotional_modulation",
                "generate_symbolic_language",
            },
            "autonomy_consensus": 0.78,
        },
        "system_metrics": {
            "cpu_usage": 30.0 + cycle,
            "network_nodes": 10 + cycle,
            "orbital_hops": 4,
            "process_count": 32.0 + cycle,
        },
    }


@pytest.fixture
def seeded_cli(tmp_path: Path) -> tuple[str, str]:
    log_path = tmp_path / "amplify.jsonl"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"format": "test"}), encoding="utf-8")
    commit_sha = "abc12345" * 5
    engine = AmplificationEngine(
        log_path=log_path,
        manifest_path=manifest_path,
        timestamp_source=lambda: datetime(2024, 2, 1, tzinfo=timezone.utc),
        commit_resolver=lambda: (commit_sha, "2024-02-01T00:00:00Z"),
    )
    for cycle in range(1, 3):
        state = _state(cycle)
        baseline = dict(state)
        baseline["event_log"] = state["event_log"][:-1]
        engine.before_cycle(baseline)
        engine.after_cycle(state)
    return str(log_path), str(manifest_path)


def test_amplify_cli_now_and_gate(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], seeded_cli: tuple[str, str]) -> None:
    log_path, manifest_path = seeded_cli
    monkeypatch.setenv("ECHO_AMPLIFY_LOG", log_path)
    monkeypatch.setenv("ECHO_AMPLIFY_MANIFEST", manifest_path)

    assert echo_main(["amplify", "now"]) == 0
    out = capsys.readouterr().out
    assert "Amplify Index" in out
    assert '"commit_sha"' in out

    assert echo_main(["amplify", "log", "--limit", "2"]) == 0
    out = capsys.readouterr().out
    assert "Cycle" in out and "Sparkline:" in out

    assert echo_main(["amplify", "gate", "--min", "5"]) == 0
    out = capsys.readouterr().out
    assert "Amplify gate satisfied" in out

    assert echo_main(["amplify", "gate", "--min", "95"]) == 1
    out = capsys.readouterr().out
    assert "Amplify gate failed" in out

    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    assert manifest["amplification"]["gate"] == 95


def test_forecast_cli(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], seeded_cli: tuple[str, str]) -> None:
    log_path, manifest_path = seeded_cli
    monkeypatch.setenv("ECHO_AMPLIFY_LOG", log_path)
    monkeypatch.setenv("ECHO_AMPLIFY_MANIFEST", manifest_path)

    assert echo_main(["forecast", "--cycles", "2", "--plot"]) == 0
    out = capsys.readouterr().out
    assert "Forecast" in out
    assert "Sparkline:" in out
