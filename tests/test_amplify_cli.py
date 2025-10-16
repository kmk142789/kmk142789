from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

import pytest

from echo.amplify import AmplificationEngine
from echo.evolver import EvolverState
from echo.manifest_cli import main as cli_main


def _state_with_cycle(cycle: int, novelty: str) -> EvolverState:
    state = EvolverState()
    state.cycle = cycle
    state.mythocode = ["alpha", novelty, "gamma"]
    state.system_metrics.cpu_usage = 38.0 + cycle
    state.system_metrics.network_nodes = 15 + cycle
    state.system_metrics.orbital_hops = 3 + cycle % 2
    state.network_cache["completed_steps"] = {
        "advance_cycle",
        "mutate_code",
        "emotional_modulation",
        "generate_symbolic_language",
        "invent_mythocode",
        "system_monitor",
        "quantum_safe_crypto",
        "evolutionary_narrative",
        "store_fractal_glyphs",
        "propagate_network",
        "decentralized_autonomy",
        "inject_prompt_resonance",
    }
    return state


def _time_sequence(*values: float) -> Iterator[float]:
    for value in values:
        yield value
    while True:
        yield values[-1]


def test_amplify_now_outputs_digest(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    times = _time_sequence(1_700_000_000.0, 1_700_000_060.0)
    engine = AmplificationEngine(
        repo_root=tmp_path,
        time_source=lambda: next(times),
        commit_resolver=lambda: "abc123",
    )
    state = _state_with_cycle(1, "beta")
    engine.ensure_snapshot(state, cycle_start=0.0, total_steps=12, persist=True)

    (tmp_path / "echo_manifest.json").write_text("{}", encoding="utf-8")
    exit_code = cli_main(["amplify", "now", "--root", str(tmp_path), "--update-manifest"])
    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "Amplify Index" in captured
    assert "Digest:" in captured
    payload = captured.strip().splitlines()[-2]
    record = json.loads(payload)
    assert record["cycle"] == 1

    manifest = json.loads((tmp_path / "echo_manifest.json").read_text(encoding="utf-8"))
    assert manifest["amplification"]["latest"]["cycle"] == 1


def test_amplify_log_and_gate(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    times = _time_sequence(1_700_000_000.0, 1_700_000_060.0, 1_700_000_120.0)
    engine = AmplificationEngine(
        repo_root=tmp_path,
        time_source=lambda: next(times),
        commit_resolver=lambda: "abc123",
    )
    engine.ensure_snapshot(_state_with_cycle(1, "beta"), cycle_start=0.0, total_steps=12, persist=True)
    engine.ensure_snapshot(_state_with_cycle(2, "delta"), cycle_start=0.0, total_steps=12, persist=True)

    exit_code = cli_main(["amplify", "log", "--root", str(tmp_path), "--limit", "5"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Cycle" in output
    assert " 2 " in output

    fail_code = cli_main(["amplify", "gate", "--root", str(tmp_path), "--min", "95"])
    fail_output = capsys.readouterr().out
    assert fail_code == 1
    assert "❌" in fail_output

    pass_code = cli_main(["amplify", "gate", "--root", str(tmp_path), "--min", "10"])
    pass_output = capsys.readouterr().out
    assert pass_code == 0
    assert "✅" in pass_output


def test_forecast_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    times = _time_sequence(
        1_700_000_000.0,
        1_700_000_030.0,
        1_700_000_060.0,
        1_700_000_090.0,
    )
    engine = AmplificationEngine(
        repo_root=tmp_path,
        time_source=lambda: next(times),
        commit_resolver=lambda: "feedface",
    )
    for cycle, novelty in enumerate(["alpha", "beta", "delta"], start=1):
        engine.ensure_snapshot(
            _state_with_cycle(cycle, novelty), cycle_start=0.0, total_steps=12, persist=True
        )

    exit_code = cli_main(["forecast", "--root", str(tmp_path), "--cycles", "3", "--plot"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Step" in output
    assert "Forecast:" in output
