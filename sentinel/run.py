from __future__ import annotations

import argparse
from pathlib import Path

from . import inventory
from .attest import attest_reports
from .required_actions import write_required_actions
from .remedy.plan import build_plan
from .signals import sentinel_workspace
from .utils import write_json
from .probe.__main__ import _build_runner, _render_sarif


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full Sentinel sweep")
    parser.add_argument("--all", action="store_true", help="Run inventory, probes, attestations, remedies")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--registry", type=Path, required=False)
    return parser.parse_args(argv)


def run_all(dry_run: bool, registry: Path | None) -> None:
    workspace = sentinel_workspace()
    inventory_path = workspace / "inventory.json"
    receipts_dir = Path("build/dominion/receipts")
    lineage_path = Path("build/lineage/lineage.json")

    payload = inventory.build_inventory(lineage_path, receipts_dir, registry)
    inventory.write_inventory(payload, inventory_path)

    runner = _build_runner()
    reports = runner.run(payload)
    report_dir = workspace / "probe_reports"
    runner.write(reports, report_dir)
    sarif = _render_sarif(reports)
    write_json(report_dir / "sentinel-probes.sarif", sarif)
    write_required_actions(reports, workspace / "required-actions")

    attest_dir = workspace / "attestations"
    attest_reports(report_dir, attest_dir)

    plan_dir = workspace / "remedy"
    plan = build_plan(report_dir, registry, dry_run)
    write_json(plan_dir / "remedy-plan.json", plan)


def main(argv: list[str] | None = None) -> int:
    options = parse_args(argv)
    if options.all:
        run_all(options.dry_run, options.registry)
        print("Sentinel full sweep completed")
    else:
        print("No action requested. Pass --all to execute the pipeline.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
