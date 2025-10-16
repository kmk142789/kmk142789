from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.echo_manifest import main as manifest_main


def _setup_repo(tmp_path: Path) -> Path:
    (tmp_path / "echo").mkdir()
    (tmp_path / "tests").mkdir()
    engine = tmp_path / "echo" / "sample_engine.py"
    engine.write_text("def run():\n    return True\n", encoding="utf-8")
    test_file = tmp_path / "tests" / "test_sample_engine.py"
    test_file.write_text("from echo import sample_engine\n", encoding="utf-8")
    (tmp_path / "echo" / "akit" / "core").mkdir(parents=True, exist_ok=True)
    (tmp_path / "echo" / "akit" / "core" / "__init__.py").write_text("def ping(): pass\n", encoding="utf-8")
    (tmp_path / "manifest").mkdir(exist_ok=True)
    (tmp_path / "manifest" / "sample.json").write_text("{}", encoding="utf-8")
    (tmp_path / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text("name: ci\n", encoding="utf-8")
    (tmp_path / "pulse_history.json").write_text("[]", encoding="utf-8")
    return tmp_path / "echo_manifest.json"


def test_cli_generate_validate_cycle(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    manifest_path = _setup_repo(tmp_path)
    result = manifest_main(
        [
            "--repo-root",
            str(tmp_path),
            "generate",
            "--output",
            str(manifest_path),
        ]
    )
    assert result == 0
    assert manifest_path.exists()

    result = manifest_main(
        [
            "--repo-root",
            str(tmp_path),
            "validate",
            "--manifest",
            str(manifest_path),
        ]
    )
    assert result == 0
    captured = capsys.readouterr()
    assert "Manifest is valid" in captured.out


def test_cli_validate_failure(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    manifest_path = _setup_repo(tmp_path)
    manifest_main(
        [
            "--repo-root",
            str(tmp_path),
            "generate",
            "--output",
            str(manifest_path),
        ]
    )
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["version"] = "9.9.9"
    manifest_path.write_text(json.dumps(data), encoding="utf-8")
    result = manifest_main(
        [
            "--repo-root",
            str(tmp_path),
            "validate",
            "--manifest",
            str(manifest_path),
        ]
    )
    assert result == 1
    captured = capsys.readouterr()
    assert "Run `echo manifest update`" in captured.out


def test_cli_update_is_idempotent(tmp_path: Path) -> None:
    manifest_path = _setup_repo(tmp_path)
    first = manifest_main(
        [
            "--repo-root",
            str(tmp_path),
            "update",
            "--manifest",
            str(manifest_path),
        ]
    )
    second = manifest_main(
        [
            "--repo-root",
            str(tmp_path),
            "update",
            "--manifest",
            str(manifest_path),
        ]
    )
    assert first == 0
    assert second == 0
