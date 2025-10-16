from __future__ import annotations

import json
from pathlib import Path

import pytest

from echo.manifest import build_manifest, verify_manifest, write_manifest


def test_deterministic_build() -> None:
    manifest_one = build_manifest()
    manifest_two = build_manifest()
    assert json.dumps(manifest_one, sort_keys=True) == json.dumps(manifest_two, sort_keys=True)
    assert manifest_one["fingerprint"] == manifest_two["fingerprint"]


def test_refresh_and_verify(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "echo_manifest.json"
    monkeypatch.setenv("ECHO_TEST_TMP", str(tmp_path))
    write_manifest(path)
    assert path.exists()
    assert verify_manifest(path) is True

    data = json.loads(path.read_text())
    data["meta"]["generator"] = "tampered"
    path.write_text(json.dumps(data))
    assert verify_manifest(path) is False
