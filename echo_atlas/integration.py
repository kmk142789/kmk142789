"""Integration helpers for other Echo modules."""

from __future__ import annotations

from pathlib import Path


def latest_report_summary(root: Path | None = None) -> str | None:
    root = root or Path.cwd()
    report = root / "docs" / "ATLAS_REPORT.md"
    if not report.exists():
        return None
    lines = report.read_text(encoding="utf-8").splitlines()
    for line in lines:
        if line.startswith("Atlas tracks"):
            return line
    for line in lines:
        if line.startswith("# "):
            continue
        if line:
            return line
    return None
