from __future__ import annotations

import json
from pathlib import Path

import pytest

from echo.manifest_cli import build_manifest, refresh_manifest, verify_manifest


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
