from __future__ import annotations

import json
from pathlib import Path

import pytest

from echo.manifest import MANIFEST_PATH, build_manifest, verify_manifest, write_manifest


def test_deterministic_build(tmp_path: Path):
    # write twice → identical bytes
    m1 = build_manifest()
    m2 = build_manifest()
    assert json.dumps(m1, sort_keys=True) == json.dumps(m2, sort_keys=True)
    assert m1["fingerprint"] == m2["fingerprint"]


def test_refresh_and_verify(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "echo_manifest.json"
    monkeypatch.setenv("ECHO_TEST_TMP", str(tmp_path))
    write_manifest(path)
    assert path.exists()
    assert verify_manifest(path) is True
    # Introduce drift
    data = json.loads(path.read_text())
    data["meta"]["generator"] = "tampered"
    path.write_text(json.dumps(data))
    assert verify_manifest(path) is False
