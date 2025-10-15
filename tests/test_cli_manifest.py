from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.echo_manifest import generate_manifest_data

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def repo_with_engine(tmp_path: Path) -> Path:
    repo = tmp_path
    (repo / "echo").mkdir()
    (repo / "tests").mkdir()
    (repo / "echo" / "beta_engine.py").write_text(
        "def main():\n    return 'beta'\n",
        encoding="utf-8",
    )
    (repo / "tests" / "test_beta_engine.py").write_text(
        "def test_beta_engine():\n    assert True\n",
        encoding="utf-8",
    )
    return repo


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, "tools/echo_manifest.py", *args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
    )
    return result


def test_cli_generate_and_validate(repo_with_engine: Path, tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    result = _run_cli([
        "generate",
        "--repo",
        str(repo_with_engine),
        "--output",
        str(manifest_path),
    ])
    assert result.returncode == 0, result.stderr
    assert manifest_path.exists()

    validate = _run_cli([
        "validate",
        "--repo",
        str(repo_with_engine),
        "--manifest",
        str(manifest_path),
    ])
    assert validate.returncode == 0, validate.stderr


def test_cli_detects_drift(repo_with_engine: Path, tmp_path: Path) -> None:
    manifest = generate_manifest_data(repo_with_engine).payload
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    broken = json.loads(manifest_path.read_text(encoding="utf-8"))
    broken["version"] = "0.0.1"
    manifest_path.write_text(json.dumps(broken), encoding="utf-8")

    validate = _run_cli([
        "validate",
        "--repo",
        str(repo_with_engine),
        "--manifest",
        str(manifest_path),
    ])
    assert validate.returncode == 1
    assert "Run echo manifest update" in validate.stderr
