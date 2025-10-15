"""Command line interface for the Assistant Kit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from .config import DEFAULT_PLAN_FILE
from .core import plan as plan_api
from .core import report as report_api
from .core import run as run_api
from .core import snapshot as snapshot_api
from .models import ExecutionPlan, plan_from_dict
from .persistence import ensure_paths_allowed


def _load_plan_from_file(path: Path) -> ExecutionPlan:
    data = json.loads(path.read_text(encoding="utf-8"))
    return plan_from_dict(data)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Assistant Kit orchestration")
    parser.set_defaults(command="run")
    parser.add_argument("--plan", type=Path, help="Path to plan JSON (defaults to latest plan)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without writing state")
    parser.add_argument("--cycles", type=int, default=1, help="Number of cycles to execute")
    parser.add_argument("--limit-artifacts", type=int, help="Maximum cycle artifacts to retain")
    parser.add_argument("--output", type=Path, help="Optional path to write JSON output")

    subparsers = parser.add_subparsers(dest="command")

    plan_parser = subparsers.add_parser("plan", help="Generate a plan for the provided intention")
    plan_parser.add_argument("intention", help="High-level intention to plan for")
    plan_parser.add_argument("--constraint", action="append", dest="constraints", help="Optional constraint")
    plan_parser.add_argument("--output", type=Path, help="Where to persist the generated plan")
    plan_parser.set_defaults(command="plan")

    report_parser = subparsers.add_parser("report", help="Show the latest AKit report")
    report_parser.add_argument("--output", type=Path, help="Where to write the report JSON")
    report_parser.set_defaults(command="report")

    snapshot_parser = subparsers.add_parser("snapshot", help="Create a deterministic snapshot")
    snapshot_parser.add_argument(
        "--output",
        type=Path,
        help="Directory where the manifest and attestation should be copied",
    )
    snapshot_parser.set_defaults(command="snapshot")

    return parser


def _write_output(path: Path, payload: dict) -> None:
    ensure_paths_allowed([path])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _handle_plan(args: argparse.Namespace) -> int:
    plan_obj = plan_api(args.intention, constraints=args.constraints)
    output_payload = plan_obj.to_dict()
    if args.output:
        _write_output(args.output, output_payload)
    print(json.dumps(output_payload, indent=2))
    return 0


def _handle_run(args: argparse.Namespace) -> int:
    plan_path = args.plan or DEFAULT_PLAN_FILE
    if plan_path.exists():
        plan_obj = _load_plan_from_file(plan_path)
    else:
        plan_obj = plan_api("Assistant Kit baseline cycle")
    try:
        result = run_api(
            plan_obj,
            cycles=args.cycles,
            dry_run=args.dry_run,
            limit_artifacts=args.limit_artifacts,
        )
    except PermissionError as error:
        print(str(error), file=sys.stderr)
        return 2
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    payload = result.to_dict()
    manifest_path, attestation_path = snapshot_api(state=result.state)
    payload["snapshot"] = {
        "manifest": str(manifest_path),
        "attestation": str(attestation_path),
    }
    if args.output:
        _write_output(args.output, payload)
    print(json.dumps(result.report.to_dict(), indent=2))
    print(
        json.dumps(
            {"manifest": str(manifest_path), "attestation": str(attestation_path)},
            indent=2,
        )
    )
    if result.report.requires_codeowners and args.dry_run:
        print("CODEOWNERS approval required before non-dry execution.", file=sys.stderr)
    return 0


def _handle_report(args: argparse.Namespace) -> int:
    rep = report_api()
    payload = rep.to_dict()
    if args.output:
        _write_output(args.output, payload)
    print(json.dumps(payload, indent=2))
    return 0


def _handle_snapshot(args: argparse.Namespace) -> int:
    manifest_path, attestation_path = snapshot_api()
    if args.output:
        ensure_paths_allowed([args.output])
        args.output.mkdir(parents=True, exist_ok=True)
        target_manifest = args.output / manifest_path.name
        target_attest = args.output / attestation_path.name
        target_manifest.write_text(manifest_path.read_text(encoding="utf-8"), encoding="utf-8")
        target_attest.write_text(attestation_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(json.dumps({"manifest": str(manifest_path), "attestation": str(attestation_path)}, indent=2))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "plan":
        return _handle_plan(args)
    if args.command == "report":
        return _handle_report(args)
    if args.command == "snapshot":
        return _handle_snapshot(args)
    return _handle_run(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
