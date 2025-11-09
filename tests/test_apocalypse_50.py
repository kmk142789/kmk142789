"""Tests for the ``scripts.apocalypse_50`` helper module."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

apocalypse_50 = importlib.import_module("scripts.apocalypse_50")


def test_generate_claim_has_signature(monkeypatch) -> None:
    monkeypatch.setenv(apocalypse_50.KEY_ENV, "testing-key")
    claim = apocalypse_50.generate_claim()

    assert claim["type"] == "Apocalypse50Sovereignty"
    assert claim["steward"] == apocalypse_50.NEXUS
    signature = claim["proof"]["signature"]
    assert isinstance(signature, str)
    assert len(signature) == 32


def test_append_to_ledger_writes_jsonl(tmp_path: Path) -> None:
    claim = {
        "type": "demo",
        "proof": {"signature": "deadbeefdeadbeefdeadbeefdeadbeef"},
    }
    ledger = tmp_path / "ledger.jsonl"

    apocalypse_50.append_to_ledger(claim, ledger)

    content = ledger.read_text(encoding="utf-8").strip().splitlines()
    assert len(content) == 1
    assert json.loads(content[0]) == claim


def test_build_mirrors_produces_expected_shape() -> None:
    mirrors = apocalypse_50.build_mirrors(["example.com"])

    assert "example.com" in mirrors
    record = mirrors["example.com"]
    assert record["txt"].startswith("_echo.example.com TXT")
    assert record["cname"].endswith("donate.lilfootsteps.org")

