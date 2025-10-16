"""Tests for the auto-release utilities."""

from __future__ import annotations

import json

from echo.auto_release import bump_version, determine_bump, prepare_release


def _states(cycle: int) -> dict:
    return {"cycle": cycle, "resonance": 1.0, "amplification": 1.0, "snapshots": []}


def test_determine_bump_major_minor_patch():
    previous = {"engines": [{"name": "A"}], "states": _states(1), "kits": []}
    current = {"engines": [{"name": "B"}], "states": _states(1), "kits": []}
    assert determine_bump(previous, current) == "major"
    current_minor = {"engines": [{"name": "A"}], "states": _states(2), "kits": []}
    assert determine_bump(previous, current_minor) == "minor"
    assert bump_version("1.2.3", "minor") == "1.3.0"


def test_prepare_release_creates_sbom(tmp_path):
    previous = {
        "engines": [{"name": "A"}],
        "states": _states(1),
        "kits": [],
    }
    current = {
        "engines": [{"name": "A"}, {"name": "B"}],
        "states": _states(1),
        "kits": [{"name": "kit"}],
    }
    prev_path = tmp_path / "prev.json"
    curr_path = tmp_path / "curr.json"
    prev_path.write_text(json.dumps(previous), encoding="utf-8")
    curr_path.write_text(json.dumps(current), encoding="utf-8")
    artifacts = prepare_release(
        current_manifest=curr_path,
        previous_manifest=prev_path,
        current_version="1.0.0",
        commits=["Add engine"],
    )
    assert artifacts.version == "2.0.0"
    assert artifacts.sbom_path.exists()
    sbom = json.loads(artifacts.sbom_path.read_text(encoding="utf-8"))
    assert sbom["bomFormat"] == "CycloneDX"
