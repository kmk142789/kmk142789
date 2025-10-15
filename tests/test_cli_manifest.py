"""CLI tests for echo manifest commands."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_FILE = REPO_ROOT / "schema" / "echo_manifest.schema.json"


def _prepare_repo(tmp_path: Path) -> None:
    (tmp_path / "schema").mkdir(parents=True, exist_ok=True)
    shutil.copy2(SCHEMA_FILE, tmp_path / "schema" / "echo_manifest.schema.json")

    (tmp_path / "echo").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tests").mkdir(parents=True, exist_ok=True)

    (tmp_path / "echo" / "sample_engine.py").write_text(
        """def main():\n    return 'sample'\n""",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_sample.py").write_text(
        """def test_sample():\n    assert True\n""",
        encoding="utf-8",
    )


def _run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "tools.echo_manifest", *args],
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_cli_generate_and_validate(tmp_path: Path) -> None:
    _prepare_repo(tmp_path)
    manifest_path = tmp_path / "echo_manifest.json"

    result = _run_cli(
        "generate",
        "--root",
        str(tmp_path),
        "--manifest",
        str(manifest_path),
        "--schema",
        str(tmp_path / "schema" / "echo_manifest.schema.json"),
        "--reuse-timestamp",
    )
    assert result.returncode == 0, result.stderr
    assert manifest_path.exists()

    validate_result = _run_cli(
        "validate",
        "--root",
        str(tmp_path),
        "--manifest",
        str(manifest_path),
        "--schema",
        str(tmp_path / "schema" / "echo_manifest.schema.json"),
    )
    assert validate_result.returncode == 0, validate_result.stderr


def test_echo_cli_update_and_stale_detection(tmp_path: Path) -> None:
    _prepare_repo(tmp_path)
    schema_path = tmp_path / "schema" / "echo_manifest.schema.json"
    manifest_path = tmp_path / "echo_manifest.json"

    update_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "echo.cli",
            "manifest",
            "update",
            "--root",
            str(tmp_path),
            "--schema",
            str(schema_path),
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert update_result.returncode == 0, update_result.stderr
    original_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Introduce staleness by editing the manifest directly.
    mutated = dict(original_manifest)
    mutated["engines"] = []
    manifest_path.write_text(json.dumps(mutated), encoding="utf-8")

    validate_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "echo.cli",
            "manifest",
            "validate",
            "--root",
            str(tmp_path),
            "--schema",
            str(schema_path),
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert validate_result.returncode != 0
    assert "stale" in validate_result.stderr.lower()
