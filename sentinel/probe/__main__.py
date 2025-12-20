from __future__ import annotations

import argparse
from pathlib import Path

from ..utils import write_json, read_json
from . import ProbeReport, ProbeRunner
from .archive import ArchiveProbe
from .fs import FileSystemProbe
from .git import GitProbe
from .http import HttpProbe
from .watcher import AutonomousWatcherProbe


def _build_runner() -> ProbeRunner:
    probes = [FileSystemProbe(), GitProbe(), HttpProbe(), ArchiveProbe(), AutonomousWatcherProbe()]
    return ProbeRunner(probes)


def _render_sarif(reports: list[ProbeReport]) -> dict:
    results = []
    rules = []
    for report in reports:
        for finding in report.findings:
            rule_id = f"{report.name}:{finding.subject}"
            rules.append({"id": rule_id, "name": report.name})
            results.append(
                {
                    "ruleId": rule_id,
                    "level": finding.sarif_level(),
                    "message": {"text": finding.message},
                    "properties": finding.data,
                }
            )
    return {
        "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": "sentinel", "rules": rules}},
                "results": results,
            }
        ],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Sentinel probes")
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=False)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    options = parse_args(argv)
    inventory = read_json(options.inventory)
    runner = _build_runner()
    reports = runner.run(inventory)
    runner.write(reports, options.report_dir)
    sarif = _render_sarif(reports)
    write_json(options.report_dir / "sentinel-probes.sarif", sarif)
    print(f"Sentinel probe reports written to {options.report_dir}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
