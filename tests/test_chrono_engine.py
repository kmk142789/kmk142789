from __future__ import annotations

import json
from pathlib import Path

import pytest

from chrono_engine import ChronoEngine, ChronoRecord, ChronoVisor


def _write_record(root: Path, rel_path: str, payload: dict) -> Path:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_chrono_engine_builds_cycle(tmp_path: Path) -> None:
    _write_record(tmp_path, "records/alpha.json", {"value": 1})
    _write_record(tmp_path, "records/beta.json", {"value": 2})

    engine = ChronoEngine(tmp_path)
    records = engine.discover_records("records/*.json")
    cycle = engine.build_cycle(records)

    cycle_path = tmp_path / "build" / "chronos" / "cycle_00001.json"
    manifest_path = tmp_path / "build" / "chronos" / "cycle_00001_records.json"
    assert cycle_path.exists()
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text())
    assert manifest[0]["rel_path"].startswith("records/")
    assert cycle["artifact_total"] == 2

    visor = ChronoVisor(tmp_path)
    timeline = visor.render_timeline()
    assert "Chrono visor timeline" in timeline
    assert "cycle 00001" in timeline


def test_chrono_visor_renders_reverse_timeline(tmp_path: Path) -> None:
    _write_record(tmp_path, "records/first.json", {"value": "alpha"})
    _write_record(tmp_path, "records/second.json", {"value": "beta"})

    engine = ChronoEngine(tmp_path)
    records = engine.discover_records("records/*.json")
    engine.build_cycle(records)

    visor = ChronoVisor(tmp_path)
    timeline = visor.render_timeline(reverse=True).splitlines()

    assert timeline[0].startswith("Chrono visor timeline (newest → oldest)")
    assert "ordinal 00002" in timeline[1]
    assert "ordinal 00001" in timeline[2]


def test_chrono_record_rejects_outside_root(tmp_path: Path) -> None:
    outside = tmp_path.parent / "external.json"
    outside.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        ChronoRecord.from_file(tmp_path, "../external.json")

