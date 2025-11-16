from __future__ import annotations

import json
from pathlib import Path

import pytest

from echo.resonance_complex import (
    ResonanceComplex,
    build_blueprint_template,
    load_resonance_blueprint,
    save_resonance_report,
)


def _write_blueprint(tmp_path: Path) -> Path:
    data = build_blueprint_template()
    path = tmp_path / "blueprint.json"
    path.write_text(json.dumps(data))
    return path


def test_load_and_simulate_resonance(tmp_path: Path) -> None:
    blueprint_path = _write_blueprint(tmp_path)
    complex_model = load_resonance_blueprint(blueprint_path)
    report = complex_model.simulate(cycles=5, seed=42)

    assert report.summary["cycles"] == 5
    assert report.summary["nodes"] == 3
    assert len(report.snapshots) == 5
    assert report.summary["peak_energy"] >= report.summary["average_energy"]


def test_save_report(tmp_path: Path) -> None:
    blueprint_path = _write_blueprint(tmp_path)
    complex_model = load_resonance_blueprint(blueprint_path)
    report = complex_model.simulate(cycles=3, seed=7)
    destination = tmp_path / "report.json"

    save_resonance_report(report, destination)
    payload = json.loads(destination.read_text())

    assert payload["summary"]["cycles"] == 3
    assert len(payload["snapshots"]) == 3


def test_invalid_blueprint_errors() -> None:
    with pytest.raises(ValueError):
        ResonanceComplex.from_dict({"nodes": []})

    with pytest.raises(ValueError):
        ResonanceComplex.from_dict({"nodes": [{"name": "a", "capacity": 1.0}], "edges": [{"source": "x", "target": "y"}]})
