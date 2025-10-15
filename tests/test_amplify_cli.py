import subprocess
import sys
from pathlib import Path

from echo.amplify import AmplifyEngine
from echo.evolver import EmotionalDrive, EvolverState, SystemMetrics


def _bootstrap_history(log_path: Path, manifest_path: Path) -> None:
    engine = AmplifyEngine(
        log_path=log_path,
        manifest_path=manifest_path,
        time_source=lambda: 1_000.0,
        commit_resolver=lambda: "cli-commit",
    )

    state = EvolverState()
    state.cycle = 1
    state.emotional_drive = EmotionalDrive(joy=0.75, rage=0.12, curiosity=0.88)
    state.system_metrics = SystemMetrics(cpu_usage=22.0, network_nodes=11, process_count=34, orbital_hops=3)
    state.mythocode = ["alpha", "beta"]
    engine.before_cycle(cycle=1)
    engine.after_cycle(cycle=1, state=state, digest={"progress": 1.0})

    engine.time_source = lambda: 1_800.0  # type: ignore[assignment]
    state.cycle = 2
    state.emotional_drive = EmotionalDrive(joy=0.7, rage=0.2, curiosity=0.85)
    state.mythocode = ["alpha", "gamma"]
    state.system_metrics = SystemMetrics(cpu_usage=26.0, network_nodes=13, process_count=40, orbital_hops=5)
    engine.before_cycle(cycle=2)
    engine.after_cycle(cycle=2, state=state, digest={"progress": 0.75})


def _run_cli(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    log_path = tmp_path / "log.jsonl"
    manifest_path = tmp_path / "manifest.json"
    if not log_path.exists():
        _bootstrap_history(log_path, manifest_path)
    command = [
        sys.executable,
        "-m",
        "echo",
        "--log-path",
        str(log_path),
        "--manifest-path",
        str(manifest_path),
        *args,
    ]
    return subprocess.run(command, check=False, capture_output=True, text=True)


def test_amplify_now_is_deterministic(tmp_path: Path):
    first = _run_cli(tmp_path, "amplify", "now")
    second = _run_cli(tmp_path, "amplify", "now")
    assert first.returncode == 0
    assert second.returncode == 0
    assert first.stdout == second.stdout
    assert "Amplify Index" in first.stdout
    assert first.stdout.strip().splitlines()[-1].startswith("{")


def test_amplify_log_and_gate(tmp_path: Path):
    log_result = _run_cli(tmp_path, "amplify", "log", "--limit", "2")
    assert log_result.returncode == 0
    assert "Cycle" in log_result.stdout
    assert "Badge" in log_result.stdout

    gate_ok = _run_cli(tmp_path, "amplify", "gate", "--min", "60")
    assert gate_ok.returncode == 0

    gate_fail = _run_cli(tmp_path, "amplify", "gate", "--min", "95")
    assert gate_fail.returncode != 0
    assert "Suggested actions" in gate_fail.stdout


def test_forecast_cli_outputs_plot(tmp_path: Path):
    forecast = _run_cli(tmp_path, "forecast", "--cycles", "2", "--plot")
    assert forecast.returncode == 0
    assert "Analysed" in forecast.stdout
    assert "Sparkline" in forecast.stdout
