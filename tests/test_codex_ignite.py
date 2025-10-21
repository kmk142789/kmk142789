from __future__ import annotations

from pathlib import Path

from codex import generate_oracle_report, main


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_generate_oracle_report_creates_weight_tables() -> None:
    manifest_path = REPO_ROOT / "manifest" / "continuum_manifest.json"
    report = generate_oracle_report(
        project="Continuum Oracle",
        owner="TestOwner",
        manifest_path=manifest_path,
        weight_scenario="live-balance-board",
        prediction_focus="outcomes if weights shift",
        root=REPO_ROOT,
    )

    assert "Continuum Oracle Report — Continuum Oracle" in report
    assert "Prediction focus: outcomes if weights shift" in report
    assert "| bridge |" in report
    assert "## Most recent signal" in report


def test_codex_ignite_cli_writes_report(tmp_path: Path) -> None:
    manifest_path = REPO_ROOT / "manifest" / "continuum_manifest.json"
    output_path = tmp_path / "oracle-report.md"

    exit_code = main(
        [
            "ignite",
            "--project",
            "Continuum Oracle",
            "--owner",
            "TestOwner",
            "--inputs",
            str(manifest_path),
            "--weights",
            "live-balance-board",
            "--predict",
            "outcomes if weights shift",
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    report = output_path.read_text(encoding="utf-8")
    assert "Continuum Oracle Report — Continuum Oracle" in report
    assert "live-balance-board" in report
