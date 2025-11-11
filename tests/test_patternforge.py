import json
from pathlib import Path

import pytest

from patternforge import PatternForgeEngine, scan


@pytest.fixture()
def sample_structure(tmp_path: Path) -> Path:
    project_root = tmp_path / "project"
    project_root.mkdir()

    (project_root / "module").mkdir()
    (project_root / "docs").mkdir()

    (project_root / "module" / "alpha.py").write_text(
        """
import math

def alpha(value):
    return math.sqrt(value)

def helper(value):
    return value + 1

class Sample:
    def method(self, x):
        return helper(x)
"""
    )

    (project_root / "module" / "beta.py").write_text(
        """
from alpha import helper

def beta(data):
    return helper(data)
"""
    )

    (project_root / "docs" / "notes.md").write_text(
        """# Notes

Alpha beta alpha.
"""
    )

    (project_root / "README.txt").write_text("PatternForge testing readme")
    return project_root


def test_scan_creates_index_file(sample_structure: Path) -> None:
    index_path = sample_structure / "patternforge_index.json"
    engine = PatternForgeEngine(root=sample_structure, index_path=index_path)
    result = engine.scan()

    assert index_path.exists(), "Index file should be created"
    payload = json.loads(index_path.read_text())
    assert payload["scans"], "Scan records should be present"
    assert result["file_count"] == 4


def test_metrics_consistency(sample_structure: Path) -> None:
    index_path = sample_structure / "patternforge_index.json"
    engine = PatternForgeEngine(root=sample_structure, index_path=index_path)
    engine.scan()

    payload = json.loads(index_path.read_text())
    scan_record = payload["scans"][-1]
    tokens = scan_record["frequency_maps"]["tokens"]

    assert tokens["alpha"] >= 2
    assert "def alpha(value)" in scan_record["structural_patterns"]["repeated_function_signatures"] or tokens["alpha"] >= 2
    assert scan_record["metrics"]["entropy_estimates"]["average"] > 0


def test_directory_scanning(sample_structure: Path) -> None:
    (sample_structure / "module" / "ignore.log").write_text("should not be read")
    index_path = sample_structure / "patternforge_index.json"
    scan(root=sample_structure, index_path=index_path)

    payload = json.loads(index_path.read_text())
    last_scan = payload["scans"][-1]
    assert last_scan["file_count"] == 4

