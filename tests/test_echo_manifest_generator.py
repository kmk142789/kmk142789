from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from tools.echo_manifest import (
    MANIFEST_VERSION,
    ManifestValidationError,
    generate_manifest,
    update_manifest,
    validate_manifest,
    write_manifest,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _touch_repo(tmp_path: Path) -> None:
    _write(tmp_path / "echo" / "alpha_engine.py", "def run():\n    return True\n")
    _write(tmp_path / "echo" / "pkg" / "__init__.py", "class EchoPackage: ...\n")
    _write(tmp_path / "modules" / "demo" / "main.py", "def main():\n    pass\n")
    _write(tmp_path / "tests" / "test_alpha_engine.py", "from echo import alpha_engine\n")
    _write(tmp_path / "tests" / "test_pkg.py", "import echo.pkg\n")
    _write(tmp_path / "echo" / "akit" / "stellar" / "__init__.py", "def boost():\n    return 'ok'\n")
    _write(tmp_path / "manifest" / "sample.json", json.dumps({"ok": True}))
    _write(tmp_path / "proofs" / "artifact.txt", "echo-proof\n")
    history = [
        {"timestamp": 1_600_000_000, "message": "cycle-start", "hash": "aa"},
        {"timestamp": 1_600_000_100, "message": "cycle-finish", "hash": "bb"},
    ]
    _write(tmp_path / "pulse_history.json", json.dumps(history))
    _write(tmp_path / ".github" / "workflows" / "build.yml", "name: build\n")


def test_generate_manifest_discovers_assets(tmp_path: Path) -> None:
    _touch_repo(tmp_path)
    manifest = generate_manifest(tmp_path)

    assert manifest["version"] == MANIFEST_VERSION
    assert manifest["generated_at"] == "1970-01-01T00:00:00Z"

    engines = manifest["engines"]
    names = [engine["name"] for engine in engines]
    assert "echo.alpha_engine" in names
    assert "echo.pkg" in names
    assert "modules.demo.main" in names

    alpha = next(engine for engine in engines if engine["name"] == "echo.alpha_engine")
    assert alpha["kind"] == "engine"
    assert alpha["entrypoints"] == ["echo.alpha_engine"]
    assert alpha["tests"] == ["tests/test_alpha_engine.py"]

    states = manifest["states"]
    assert states["cycle"] == 2
    expected_resonance = round(len(engines) / max(1, len(manifest["kits"]) or 1), 3)
    unique_tests = sorted({test for engine in engines for test in engine["tests"]})
    expected_amplification = round(len(unique_tests) / max(1, len(engines)), 3)
    assert states["resonance"] == pytest.approx(expected_resonance)
    assert states["amplification"] == pytest.approx(expected_amplification)
    assert len(states["snapshots"]) == 2
    assert states["snapshots"][0]["timestamp"] == "2020-09-13T12:26:40Z"

    kits = manifest["kits"]
    assert kits[0]["name"] == "stellar"
    assert "boost" in kits[0]["capabilities"]

    artifacts = manifest["artifacts"]
    paths = [artifact["path"] for artifact in artifacts]
    assert "manifest/sample.json" in paths
    assert all(len(artifact["content_hash"]) == 12 for artifact in artifacts)

    workflows = manifest["ci"]["integration"]
    assert workflows == ["build"]

    assert manifest["meta"]["commit_sha"] == "UNKNOWN"


def test_validate_manifest_detects_stale(tmp_path: Path) -> None:
    _touch_repo(tmp_path)
    manifest = generate_manifest(tmp_path)
    manifest_path = tmp_path / "echo_manifest.json"
    write_manifest(manifest, manifest_path)

    validate_manifest(manifest_path, tmp_path)  # does not raise

    broken = dict(manifest)
    broken["version"] = "2.0.0"
    manifest_path.write_text(json.dumps(broken), encoding="utf-8")
    with pytest.raises(ManifestValidationError):
        validate_manifest(manifest_path, tmp_path)


def test_update_manifest_is_idempotent(tmp_path: Path) -> None:
    _touch_repo(tmp_path)
    manifest_path = tmp_path / "echo_manifest.json"
    update_manifest(manifest_path, tmp_path)
    first = manifest_path.read_text(encoding="utf-8")
    # Sleep to allow filesystem timestamp to change if the file were rewritten
    time.sleep(0.1)
    update_manifest(manifest_path, tmp_path)
    second = manifest_path.read_text(encoding="utf-8")
    assert first == second
