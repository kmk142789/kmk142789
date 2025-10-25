from __future__ import annotations

import json
from pathlib import Path

import pytest

from echo.manifest_cli import (
    ascend,
    build_manifest,
    main as manifest_main,
    refresh_manifest,
    verify_manifest,
)


@pytest.fixture()
def fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "echo").mkdir(parents=True)
    (repo / "docs" / "echo").mkdir(parents=True)
    (repo / "datasets").mkdir()
    (repo / ".github").mkdir()

    (repo / ".github" / "CODEOWNERS").write_text(
        "/echo/** @core-team\n/docs/** @docs-team\n* @all\n",
        encoding="utf-8",
    )

    (repo / "pyproject.toml").write_text(
        """
[project]
scripts = {echo = "echo.manifest_cli:main"}
""",
        encoding="utf-8",
    )

    (repo / "echo" / "engine_module.py").write_text(
        """class SampleEngine:
    pass


class AnotherState:
    pass
""",
        encoding="utf-8",
    )

    (repo / "echo" / "state_module.py").write_text(
        """from dataclasses import dataclass


@dataclass
class DataState:
    value: int
""",
        encoding="utf-8",
    )

    (repo / "datasets" / "sample.json").write_text("{}\n", encoding="utf-8")
    (repo / "docs" / "echo" / "manifest.md").write_text("# Manifest\n", encoding="utf-8")

    return repo


def _read_golden(name: str) -> str:
    golden_path = Path(__file__).with_name("data") / name
    return golden_path.read_text(encoding="utf-8")


def _prepare_timeline_inputs(repo: Path) -> None:
    (repo / "state").mkdir(parents=True, exist_ok=True)
    (repo / "data").mkdir(parents=True, exist_ok=True)

    (repo / "state" / "amplify_log.jsonl").write_text(
        "{" "\"cycle\": 1, \"index\": 1.0, \"timestamp\": "
        "\"2024-01-01T00:00:00+00:00\", \"commit_sha\": \"\"}" "\n",
        encoding="utf-8",
    )
    (repo / "pulse_history.json").write_text(
        "[{\"timestamp\": 1704067200, \"message\": \"Pulse:Alpha\", \"hash\": \"abc\"}]\n",
        encoding="utf-8",
    )
    (repo / "data" / "puzzle_index.json").write_text(
        "{" "\"puzzles\": [{\"id\": 1, \"doc\": \"docs/echo/manifest.md\","
        " \"title\": \"Test\", \"script_type\": \"p2pkh\","
        " \"address\": \"\", \"status\": \"active\"}]}\n",
        encoding="utf-8",
    )
    (repo / "data" / "bridge_harmonics.json").write_text(
        "{" "\"harmonics\": [{\"cycle\": 1, \"signature\": \"sig\","
        " \"threads\": [{\"name\": \"thread\", \"resonance\": 0.5,"
        " \"harmonics\": [\"alpha\"]}]}]}\n",
        encoding="utf-8",
    )


def test_build_manifest_matches_golden(fixture_repo: Path) -> None:
    manifest = build_manifest(repo_root=fixture_repo)
    expected = json.loads(_read_golden("fixture_manifest.json"))
    assert manifest == expected


def test_verify_manifest_detects_tamper(fixture_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    manifest_path = refresh_manifest(repo_root=fixture_repo)
    assert verify_manifest(manifest_path, repo_root=fixture_repo)

    target_file = fixture_repo / "datasets" / "sample.json"
    target_file.write_text('{"changed": true}\n', encoding="utf-8")

    assert not verify_manifest(manifest_path, repo_root=fixture_repo)
    captured = capsys.readouterr()
    assert "Digest mismatch" in captured.out


def test_ascend_full_refreshes_manifest_and_timeline(fixture_repo: Path) -> None:
    _prepare_timeline_inputs(fixture_repo)

    summary = ascend(
        project_root=fixture_repo,
        include_manifest=True,
        include_timeline=True,
    )

    manifest_path = Path(summary["manifest"])
    assert manifest_path.exists()

    timeline = summary["timeline"]
    assert timeline["cycles"] == 1
    assert timeline["latest_cycle"] == 1
    output_dir = Path(timeline["output_dir"])
    assert (output_dir / "cycle_timeline.json").exists()
    assert (output_dir / "cycle_timeline.md").exists()


def test_cli_ascend_full_command(fixture_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _prepare_timeline_inputs(fixture_repo)

    exit_code = manifest_main(
        [
            "ascend",
            "--full",
            "--root",
            str(fixture_repo),
        ]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Manifest refreshed" in output
    assert "Cycle timeline refreshed" in output
