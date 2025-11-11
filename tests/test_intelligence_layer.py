from __future__ import annotations

import json
from importlib import reload
from pathlib import Path

from echo import echo_capability_engine as engine
from echo.ecosystem_pulse import EcosystemAreaConfig
from echo.intelligence_layer import (
    IntelligenceLayerSnapshot,
    synthesize_intelligence_layer,
)


def _seed_manifest(root: Path) -> Path:
    manifest_path = root / "echo_manifest.json"
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
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    return manifest_path


def _seed_files(root: Path) -> None:
    (root / "echo" / "core").mkdir(parents=True, exist_ok=True)
    (root / "echo" / "core" / "engine_alpha.py").write_text("", encoding="utf-8")
    (root / "echo" / "docs").mkdir(parents=True, exist_ok=True)
    (root / "echo" / "docs" / "doc_alpha.md").write_text("guide", encoding="utf-8")
    (root / "pulse" / "state").mkdir(parents=True, exist_ok=True)
    (root / "pulse" / "state" / "state_beta.json").write_text("{}", encoding="utf-8")

    docs_dir = root / "docs"
    docs_dir.mkdir(exist_ok=True)
    (docs_dir / "REPO_OVERVIEW.md").write_text("overview", encoding="utf-8")
    (docs_dir / "handbook.md").write_text("handbook", encoding="utf-8")

    (root / "README.md").write_text("# root", encoding="utf-8")

    ops_dir = root / "ops"
    ops_dir.mkdir(exist_ok=True)
    (ops_dir / "runbook.md").write_text("runbook", encoding="utf-8")


def test_synthesize_intelligence_layer(tmp_path: Path) -> None:
    _seed_files(tmp_path)
    manifest = _seed_manifest(tmp_path)

    areas = (
        EcosystemAreaConfig(
            key="docs",
            title="Docs",
            relative_path=Path("docs"),
            description="Documentation and reference material.",
            required=(Path("docs/REPO_OVERVIEW.md"), Path("README.md")),
            freshness_days=90,
            volume_hint=2,
        ),
        EcosystemAreaConfig(
            key="ops",
            title="Ops",
            relative_path=Path("ops"),
            description="Operational guides.",
            required=(Path("ops"),),
            freshness_days=30,
            volume_hint=3,
        ),
    )

    snapshot = synthesize_intelligence_layer(
        manifest_path=manifest,
        repo_root=tmp_path,
        momentum_samples=[0.02, 0.05, 0.08, 0.04],
        momentum_threshold=0.01,
        ecosystem_areas=areas,
    )

    assert isinstance(snapshot, IntelligenceLayerSnapshot)
    payload = snapshot.to_dict()

    assert payload["mesh"]["summary"]["total_entries"] == 4
    assert payload["momentum"]["status"] == "accelerating"
    assert len(payload["momentum"]["glyph_arc"]) == 4
    assert payload["ecosystem"]["signals"], "ecosystem report should contain signals"
    assert payload["coherence"]["coherence_score"] > 0
    assert payload["context"]["momentum_sample_count"] == 4


def test_harmonic_intelligence_layer_capability(tmp_path: Path) -> None:
    _seed_files(tmp_path)
    manifest = _seed_manifest(tmp_path)

    module = reload(engine)
    result = module.execute_capability(
        "harmonic_intelligence_layer",
        manifest_path=str(manifest),
        repo_root=str(tmp_path),
        momentum_samples=[0.02, 0.05, 0.08],
        momentum_threshold=0.01,
        ecosystem_areas=[
            {
                "key": "docs",
                "title": "Docs",
                "relative_path": "docs",
                "description": "Documentation and reference material.",
                "required": ["docs/REPO_OVERVIEW.md", "README.md"],
                "freshness_days": 90,
                "volume_hint": 2,
            },
            {
                "key": "ops",
                "title": "Ops",
                "relative_path": "ops",
                "description": "Operational guides.",
                "required": ["ops"],
                "freshness_days": 30,
                "volume_hint": 3,
            },
        ],
    )

    assert result["success"] is True
    payload = result["payload"]
    assert payload["mesh"]["summary"]["total_entries"] == 4
    assert payload["coherence"]["status"] in {"ascending", "steady", "fragmented"}
    assert payload["context"]["momentum_sample_count"] == 3
