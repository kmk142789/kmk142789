from __future__ import annotations

import json
import subprocess
from pathlib import Path


def run_quarantine(tmp_path: Path, payload: str, label: str = "payload") -> dict:
    payload_path = tmp_path / f"{label}.txt"
    payload_path.write_text(payload, encoding="utf-8")
    out_path = tmp_path / "summary.json"
    cmd = [
        "python",
        "tools/quarantine_payload.py",
        str(payload_path),
        "--labels",
        label,
        "--output",
        str(out_path),
        "--timestamp",
        "2025-05-11T00:00:00Z",
        "--note",
        "unit-test",
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    assert "Wrote 1 payload summaries" in result.stdout
    data = json.loads(out_path.read_text(encoding="utf-8"))
    return data


def test_quarantine_records_hex_payload(tmp_path: Path) -> None:
    data = run_quarantine(tmp_path, "0xdeadBEEF", label="hex")
    assert data["generated_at"] == "2025-05-11T00:00:00Z"
    assert data["note"] == "unit-test"
    entry = data["entries"][0]
    assert entry["label"] == "hex"
    assert entry["format"] == "hex-string"
    assert entry["sha256"] == "33fb67bd8981662aab8e804aacbaae286803fc1aa75f40247a7738a2a2323534"
    assert entry["size"] == 10
    assert entry["preview_start"].startswith("0xdead")
    assert entry["preview_end"].endswith("BEEF")
    assert not entry["contains_control"]


def test_quarantine_records_text_payload(tmp_path: Path) -> None:
    payload = "EchoEvolver: Nexus Evolution\nCycle 1"  # human-readable sample
    data = run_quarantine(tmp_path, payload, label="text")
    entry = data["entries"][0]
    assert entry["label"] == "text"
    assert entry["format"] == "text"
    assert entry["size"] == len(payload)
    assert entry["preview_start"].startswith("EchoEvolver")
    assert entry["preview_end"].endswith("Cycle 1")
