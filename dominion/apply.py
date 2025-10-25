"""CLI entry point for applying Dominion plans."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from .executor import PlanExecutor
from .plans import DominionPlan


def _load_plan(path: Path) -> DominionPlan:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return DominionPlan.from_dict(payload)


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Apply Dominion plans to the current workspace.")
    parser.add_argument("plans", nargs="+", help="Plan files or glob expressions.")
    parser.add_argument("--workdir", default="build/dominion", help="Execution working directory.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without modifying state.")
    args = parser.parse_args(argv)

    plan_paths: list[Path] = []
    for pattern in args.plans:
        matched = list(Path().glob(pattern))
        if not matched:
            raise SystemExit(f"No plans matched pattern: {pattern}")
        plan_paths.extend(sorted(matched))

    executor = PlanExecutor(workdir=Path(args.workdir))
    for path in plan_paths:
        plan = _load_plan(path)
        receipt = executor.apply(plan, dry_run=args.dry_run)
        print(f"{path}: {receipt.status} ({receipt.summary})")


if __name__ == "__main__":
    main()
