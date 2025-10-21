from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_codex_weave_compass_map(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_path = tmp_path / "compass-map.json"
    command = [
        sys.executable,
        str(repo_root / "codex"),
        "weave",
        "--project",
        "Continuum Compass",
        "--owner",
        "Josh+Echo",
        "--inputs",
        "oracle-report.md",
        "--schema",
        "compass-map.json",
        "--emit",
        str(output_path),
    ]
    result = subprocess.run(command, cwd=repo_root, capture_output=True, text=True, check=True)

    assert "Compass map generated" in result.stdout
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["project"] == "Continuum Compass"
    assert data["owner"] == "Josh+Echo"
    assert any(tag["label"] == "bridge" for tag in data["tags"])
