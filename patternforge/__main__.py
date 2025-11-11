"""Command line entry point for PatternForge."""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .engine import PatternForgeEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PatternForge Autonomous Pattern Discovery Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Execute a full repository scan")
    scan_parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Root directory to scan. Defaults to the repository root.",
    )
    scan_parser.add_argument(
        "--index",
        type=Path,
        default=None,
        help="Path to the patternforge index file. Defaults to patternforge_index.json at the root.",
    )
    scan_parser.add_argument(
        "--interval",
        type=float,
        default=0.0,
        help="Optional interval in seconds to repeat the scan continuously.",
    )
    return parser


def run_scan(args: argparse.Namespace) -> int:
    engine = PatternForgeEngine(root=args.root, index_path=args.index)
    if args.interval and args.interval > 0:
        while True:
            engine.scan()
            time.sleep(args.interval)
    else:
        engine.scan()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "scan":
        return run_scan(args)
    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover - CLI entry
    sys.exit(main())
