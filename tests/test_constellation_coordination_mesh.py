from __future__ import annotations

import json
from importlib import reload
from pathlib import Path

import pytest

from echo import echo_capability_engine as engine
from echo.coordination_mesh import build_coordination_mesh


@pytest.fixture()
def sample_manifest(tmp_path: Path) -> Path:
    manifest = tmp_path / "echo_manifest.json"

    # Create backing files to exercise existence tracking.
    (tmp_path / "echo" / "core").mkdir(parents=True, exist_ok=True)
    (tmp_path / "echo" / "core" / "engine_alpha.py").write_text("", encoding="utf-8")
    (tmp_path / "echo" / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "echo" / "docs" / "doc_alpha.md").write_text("", encoding="utf-8")
    (tmp_path / "pulse" / "state").mkdir(parents=True, exist_ok=True)
    (tmp_path / "pulse" / "state" / "state_beta.json").write_text("{}", encoding="utf-8")

    payload = {
        "engines": [
            {
                "name": "Engine Alpha",
                "path": "echo/core/engine_alpha.py",
                "owners": ["@alpha"],
                "tags": ["engine", "core"],
            },
            {
                "name": "Pulse Resonator",
                "path": "pulse/state/state_beta.json",
                "owners": ["@beta", "@gamma"],
            },
        ],
        "docs": [
            {
                "name": "Alpha Field Guide",
                "path": "echo/docs/doc_alpha.md",
                "owners": ["@alpha"],
            }
        ],
        "states": [
            {
                "name": "Orbital Cohesion",
                "path": "pulse/state/state_beta.json",
                "owners": ["@gamma"],
            }
        ],
    }
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    return manifest


def test_build_coordination_mesh_creates_clusters(sample_manifest: Path) -> None:
    mesh = build_coordination_mesh(sample_manifest)
    payload = mesh.as_dict()

    assert payload["summary"]["total_entries"] == 4
    assert payload["summary"]["categories"] == {"docs": 1, "engines": 2, "states": 1}
    assert payload["summary"]["modules"] == 2
    assert set(payload["summary"]["owners"]) == {"@alpha", "@beta", "@gamma"}
    assert pytest.approx(payload["summary"]["autonomy_index"], rel=1e-6) == 0.75

    clusters = {cluster["module"]: cluster for cluster in payload["clusters"]}
    assert "echo" in clusters and "pulse" in clusters
    echo_cluster = clusters["echo"]
    assert echo_cluster["categories"] == {"docs": 1, "engines": 1}
    assert echo_cluster["owners"] == {"@alpha": 2}
    assert all(entry["exists"] for entry in echo_cluster["entries"])

    links = {(link["source"], link["target"]): link["weight"] for link in payload["links"]}
    assert links[("docs", "engines")] == 1
    assert links[("engines", "states")] == 1


def test_execute_constellation_capability_uses_manifest(sample_manifest: Path) -> None:
    module = reload(engine)
    result = module.execute_capability(
        "constellation_coordination_mesh",
        manifest_path=str(sample_manifest),
    )
    assert result["success"] is True
    payload = result["payload"]
    assert payload["summary"]["total_entries"] == 4
    assert any(cluster["module"] == "pulse" for cluster in payload["clusters"])
    assert "generated_at" in payload
