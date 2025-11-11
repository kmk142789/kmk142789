from __future__ import annotations

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
    assert "Documentation" in docs_signal.description

    assert ops_signal.file_count == 0
    assert ops_signal.missing == [Path("ops")]
    assert ops_signal.score == 0
    assert any("Bootstrap" in note for note in ops_signal.insights)

    markdown = report.render_markdown()
    assert "Docs" in markdown
    assert "Ops" in markdown

    report_dict = report.to_dict()
    assert report_dict["signals"][0]["key"] in {"docs", "ops"}
    assert 0 <= report.overall_score <= 100
