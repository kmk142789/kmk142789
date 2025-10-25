"""CLI helper to build the Pulse Dashboard dataset."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pulse_dashboard import PulseDashboardBuilder


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the Pulse Dashboard dataset")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root containing pulse_history.json and attestations/",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Optional output path for the dashboard JSON (defaults to pulse_dashboard/data/dashboard.json)",
    )
    parser.add_argument(
        "--print",  # noqa: A002 - intentional flag name
        dest="print_payload",
        action="store_true",
        help="Echo the assembled payload to stdout",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    builder = PulseDashboardBuilder(project_root=args.root)
    payload = builder.build()
    output = builder.write(payload, path=args.out)
    if args.print_payload:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Pulse Dashboard written to {output}")
    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution
    raise SystemExit(main())
