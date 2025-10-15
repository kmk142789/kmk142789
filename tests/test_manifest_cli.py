from __future__ import annotations

import json
from pathlib import Path

import pytest

from echo.manifest_cli import build_manifest, refresh_manifest, verify_manifest


@pytest.fixture
def temp_manifest(tmp_path: Path) -> Path:
    return tmp_path / "manifest.json"


def test_build_manifest_contains_expected_engine() -> None:
    manifest = build_manifest()
    engines = {(entry["name"], entry["module_spec"]): entry for entry in manifest["engines"]}
    key = ("BridgeEmitter", "echo.bridge_emitter")
    assert key in engines
    bridge = engines[key]
    assert bridge["summary"].startswith("High level helper")
    assert bridge["doc_digest"]
    assert bridge["source_digest"]
    assert all(method.isidentifier() for method in bridge["public_methods"])


def test_build_manifest_states_are_sorted() -> None:
    manifest = build_manifest()
    names = [entry["name"] for entry in manifest["states"]]
    assert names == sorted(names)


def test_refresh_and_verify_round_trip(temp_manifest: Path, capsys: pytest.CaptureFixture[str]) -> None:
    refresh_manifest(temp_manifest)
    assert temp_manifest.exists()

    capsys.readouterr()
    assert verify_manifest(temp_manifest)

    payload = json.loads(temp_manifest.read_text())
    payload["states"][0]["name"] = "Broken"
    temp_manifest.write_text(json.dumps(payload))

    assert not verify_manifest(temp_manifest)
    out = capsys.readouterr().out
    assert "Manifest drift detected" in out
