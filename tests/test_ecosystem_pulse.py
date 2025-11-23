from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path

from echo.ecosystem_pulse import EcosystemAreaConfig, EcosystemPulse


def test_generate_report_with_custom_areas(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "REPO_OVERVIEW.md").write_text("overview", encoding="utf-8")
    (docs_dir / "guide.md").write_text("guide", encoding="utf-8")
    (tmp_path / "README.md").write_text("# root readme", encoding="utf-8")

    pulse = EcosystemPulse(
        repo_root=tmp_path,
        areas=[
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
        ],
    )

    report = pulse.generate_report()

    assert len(report.signals) == 2
    docs_signal = next(signal for signal in report.signals if signal.key == "docs")
    ops_signal = next(signal for signal in report.signals if signal.key == "ops")

    assert docs_signal.file_count == 2
    assert docs_signal.missing == []
    assert docs_signal.score > 0
    assert docs_signal.alert_level == "steady"
    assert "Documentation" in docs_signal.description

    assert ops_signal.file_count == 0
    assert ops_signal.missing == [Path("ops")]
    assert ops_signal.score == 0
    assert ops_signal.alert_level == "critical"
    assert any("Bootstrap" in note for note in ops_signal.insights)

    markdown = report.render_markdown()
    assert "Docs" in markdown
    assert "Ops" in markdown

    report_dict = report.to_dict()
    assert report_dict["signals"][0]["key"] in {"docs", "ops"}
    assert 0 <= report.overall_score <= 100


def test_prioritized_actions_surface_urgent_work(tmp_path: Path) -> None:
    healthy_dir = tmp_path / "core"
    healthy_dir.mkdir()
    (healthy_dir / "engine.py").write_text("core", encoding="utf-8")

    stale_dir = tmp_path / "ops"
    stale_dir.mkdir()
    stale_file = stale_dir / "runbook.md"
    stale_file.write_text("ops", encoding="utf-8")
    old_time = (datetime.now(timezone.utc) - timedelta(days=120)).timestamp()
    os.utime(stale_file, (old_time, old_time))

    pulse = EcosystemPulse(
        repo_root=tmp_path,
        areas=[
            EcosystemAreaConfig(
                key="core",
                title="Core",
                relative_path=Path("core"),
                description="Runtime core.",
                required=(Path("core/engine.py"),),
                freshness_days=30,
                volume_hint=1,
            ),
            EcosystemAreaConfig(
                key="ops",
                title="Ops",
                relative_path=Path("ops"),
                description="Operational guides.",
                required=(Path("ops/runbook.md"),),
                freshness_days=30,
                volume_hint=1,
            ),
            EcosystemAreaConfig(
                key="docs",
                title="Docs",
                relative_path=Path("docs"),
                description="Docs missing to trigger critical alert.",
                required=(Path("docs"),),
                freshness_days=30,
                volume_hint=1,
            ),
        ],
    )

    report = pulse.generate_report()
    alerts = {signal.key: signal.alert_level for signal in report.signals}

    assert alerts["core"] == "steady"
    assert alerts["ops"] == "warning"
    assert alerts["docs"] == "critical"

    actions = report.prioritized_actions(max_items=3)
    assert [action["key"] for action in actions][:2] == ["docs", "ops"]
    assert actions[0]["alert"] == "critical"
    assert "Restore missing assets" in actions[0]["next_step"]
    assert actions[1]["alert"] == "warning"

    payload = report.to_dict(include_actions=True, max_actions=2)
    assert "actions" in payload
    assert len(payload["actions"]) == 2

    markdown = report.render_markdown()
    assert "Prioritized Actions" in markdown
    assert "critical" in markdown.lower()
