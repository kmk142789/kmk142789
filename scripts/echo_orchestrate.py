"""CLI wrapper to refresh Echo substrate artifacts."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from echo.substrate import orchestrate


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Refresh Echo substrate outputs.")
    parser.add_argument("--refresh", action="store_true", help="Rebuild echo_map.json and reports.")
    parser.add_argument("--with-ud", action="store_true", help="Attempt Unstoppable Domains enrichment.")
    args = parser.parse_args(argv)

    root = ROOT
    if args.refresh:
        orchestrate(root, with_ud=args.with_ud)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
