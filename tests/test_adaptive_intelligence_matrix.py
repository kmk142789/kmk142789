from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

import adaptive_intelligence_matrix as aim


def _prepare_environment(tmp_path: Path) -> Tuple[Path, Path, Path]:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    pulse_path = tmp_path / "pulse_history.json"
    pulses = [
        {"timestamp": 1_700_000_000.0, "message": "pulse-a", "hash": "a"},
        {"timestamp": 1_700_000_600.0, "message": "pulse-b", "hash": "b"},
    ]
    pulse_path.write_text(json.dumps(pulses), encoding="utf-8")

    roadmap_path = tmp_path / "roadmap_summary.json"
    roadmap_payload = {
        "totals": {
            "overall": 6,
            "per_tag": {"TODO": 5, "FIXME": 1},
            "per_location": {"docs": 2, "tests": 1},
        }
    }
    roadmap_path.write_text(json.dumps(roadmap_payload), encoding="utf-8")

    plan_path = docs_dir / "NEXT_CYCLE_PLAN.md"
    plan_path.write_text(
        """# Next Cycle Plan\n\n## Recent Deltas\n* a1 first delta\n\n## Proposed Actions\n- Expand glyph research\n- Align registry\n\n## Success Criteria\n- [ ] Deliver glyph artifact\n""",
        encoding="utf-8",
    )

    return pulse_path, roadmap_path, plan_path


def test_matrix_report_fuses_signals(tmp_path, monkeypatch):
    pulse_path, roadmap_path, plan_path = _prepare_environment(tmp_path)
    monkeypatch.setattr(aim.time, "time", lambda: 1_700_001_200.0)

    config = aim.MatrixConfig(
        repo_root=tmp_path,
        pulse_history_path=pulse_path,
        roadmap_summary_path=roadmap_path,
        next_cycle_plan_path=plan_path,
        pulse_latency_threshold=900,
        automation_todo_threshold=4,
    )
    matrix = aim.AdaptiveIntelligenceMatrix(config)
    report = matrix.generate_report()

    assert {signal.key for signal in report.signals} == {
        "pulse_history",
        "roadmap_summary",
        "next_cycle_plan",
    }
    assert report.composite_scores["automation_pressure"] > 0
    assert report.composite_scores["signal_health"] <= 1
    text_output = report.to_text()
    assert "Adaptive Intelligence Matrix" in text_output
    assert "Roadmap Density" in text_output


def test_cli_entrypoint_emits_json(tmp_path, monkeypatch):
    pulse_path, roadmap_path, plan_path = _prepare_environment(tmp_path)
    monkeypatch.setattr(aim.time, "time", lambda: 1_700_001_500.0)

    emit_path = tmp_path / "report.json"
    aim.main(
        [
            "--repo-root",
            str(tmp_path),
            "--emit-json",
            str(emit_path),
            "--quiet",
        ]
    )

    payload = json.loads(emit_path.read_text(encoding="utf-8"))
    assert "composite_scores" in payload
    assert payload["signals"]
