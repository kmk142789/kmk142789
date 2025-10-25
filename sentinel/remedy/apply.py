from __future__ import annotations

import argparse
from pathlib import Path

from ..utils import environment_flag, isoformat, read_json, write_json


def apply_plan(path: Path, force: bool) -> bool:
    data = read_json(path)
    actions = data.get("actions", [])
    if not force and data.get("dry_run", True):
        return False

    changed = False
    for action in actions:
        if action.get("status") == "applied":
            continue
        action["status"] = "applied"
        action["applied_at"] = isoformat()
        changed = True
    if changed:
        data["dry_run"] = False
        write_json(path, data)
    return changed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply Sentinel remedy plans")
    parser.add_argument("plans", nargs="+", type=Path)
    parser.add_argument("--force", action="store_true", help="Apply even when dry-run is set")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    options = parse_args(argv)
    enable_apply = environment_flag("SENTINEL_ENABLE") or options.force
    if not enable_apply:
        print("Sentinel remedy apply skipped (enable with SENTINEL_ENABLE=1)")
        return 0

    applied_any = False
    for plan_path in options.plans:
        applied_any |= apply_plan(plan_path, force=True)
    if applied_any:
        print("Sentinel remedy actions applied")
    else:
        print("No Sentinel remedy actions required")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

