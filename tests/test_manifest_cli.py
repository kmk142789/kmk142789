from __future__ import annotations

import json
from pathlib import Path

import pytest

from echo.manifest_cli import (
    build_manifest,
    load_manifest_ledger,
    manifest_status,
    refresh_manifest,
    verify_manifest,
    verify_manifest_ledger,
)


@pytest.fixture
def temp_manifest(tmp_path: Path) -> Path:
    return tmp_path / "manifest.json"


@pytest.fixture
def temp_ledger(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    ledger_path = tmp_path / "ledger" / "manifest_history.jsonl"
    monkeypatch.setenv("ECHO_MANIFEST_LEDGER", str(ledger_path))
    return ledger_path


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


def test_refresh_and_verify_round_trip(
    temp_manifest: Path, temp_ledger: Path, capsys: pytest.CaptureFixture[str]
) -> None:
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


def test_refresh_appends_to_ledger(temp_manifest: Path, temp_ledger: Path) -> None:
    refresh_manifest(temp_manifest)
    refresh_manifest(temp_manifest)

    entries = load_manifest_ledger()
    assert len(entries) == 2
    assert entries[0]["sequence"] == 1
    assert entries[1]["sequence"] == 2
    assert entries[0]["ledger_seal"] == entries[1]["ledger_prev"]
    assert entries[0]["manifest_digest"] == entries[1]["manifest_digest"]


def test_manifest_status_and_ledger_verification(
    temp_manifest: Path, temp_ledger: Path
) -> None:
    refresh_manifest(temp_manifest)
    status = manifest_status(temp_manifest)

    assert status["manifest_exists"] is True
    assert status["ledger_entries"] == 1
    assert status["ledger_match"] is True
    assert verify_manifest_ledger(temp_manifest)


def test_manifest_ledger_detects_tampering(temp_manifest: Path, temp_ledger: Path) -> None:
    refresh_manifest(temp_manifest)
    refresh_manifest(temp_manifest)

    ledger_path = temp_ledger
    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    corrupted = json.loads(lines[0])
    corrupted["manifest_digest"] = "0" * 64
    lines[0] = json.dumps(corrupted)
    ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assert not verify_manifest_ledger(temp_manifest)
