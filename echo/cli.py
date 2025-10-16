"""Legacy compatibility CLI for the Echo project.

The primary command entry point for the ``echo`` console script now lives in
``echo.manifest_cli``.  This shim keeps the old module importable while
delegating to the new implementation.  It exposes a reduced set of commands
that mirror the previous behaviour but rely on the modern manifest helpers.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from .manifest_cli import refresh_manifest, show_manifest, verify_manifest


def _cmd_refresh(args: argparse.Namespace) -> int:
    refresh_manifest(args.path)
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    show_manifest(args.path)
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    return 0 if verify_manifest(args.path) else 1


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="echo",
        description="Echo compatibility CLI (delegates to echo.manifest_cli)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    refresh_parser = subparsers.add_parser("manifest-refresh", help="Refresh manifest")
    refresh_parser.add_argument("--path", type=Path, help="Optional manifest path")
    refresh_parser.set_defaults(func=_cmd_refresh)

    show_parser = subparsers.add_parser("manifest-show", help="Show manifest summary")
    show_parser.add_argument("--path", type=Path, help="Optional manifest path")
    show_parser.set_defaults(func=_cmd_show)

    verify_parser = subparsers.add_parser("manifest-verify", help="Verify manifest digest")
    verify_parser.add_argument("--path", type=Path, help="Optional manifest path")
    verify_parser.set_defaults(func=_cmd_verify)

    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover - script entry
    raise SystemExit(main())
