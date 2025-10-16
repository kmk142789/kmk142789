"""Unified Echo CLI exposing manifest, provenance, policy, and planning flows."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from akit import plan as akit_plan

from . import auto_release, graph, policy_engine, provenance
from .manifest_cli import refresh_manifest, show_manifest, verify_manifest


def _cmd_manifest_refresh(args: argparse.Namespace) -> int:
    refresh_manifest(args.path)
    return 0


def _cmd_manifest_show(args: argparse.Namespace) -> int:
    show_manifest(args.path)
    return 0


def _cmd_manifest_verify(args: argparse.Namespace) -> int:
    return 0 if verify_manifest(args.path) else 1


def _add_manifest_parsers(subparsers: argparse._SubParsersAction) -> None:
    """Attach manifest management commands, including legacy aliases."""

    manifest_parser = subparsers.add_parser("manifest", help="Manifest operations")
    manifest_sub = manifest_parser.add_subparsers(dest="manifest_command", required=True)

    refresh_parser = manifest_sub.add_parser("refresh", help="Regenerate the manifest")
    refresh_parser.add_argument("--path", type=Path, help="Optional manifest path")
    refresh_parser.set_defaults(func=_cmd_manifest_refresh)

    show_parser = manifest_sub.add_parser("show", help="Show manifest summary")
    show_parser.add_argument("--path", type=Path, help="Optional manifest path")
    show_parser.set_defaults(func=_cmd_manifest_show)

    verify_parser = manifest_sub.add_parser("verify", help="Verify manifest digest")
    verify_parser.add_argument("--path", type=Path, help="Optional manifest path")
    verify_parser.set_defaults(func=_cmd_manifest_verify)

    # Backwards compatibility with the historical flat command names.
    legacy_refresh = subparsers.add_parser("manifest-refresh", help="Refresh manifest (legacy)")
    legacy_refresh.add_argument("--path", type=Path, help="Optional manifest path")
    legacy_refresh.set_defaults(func=_cmd_manifest_refresh)

    legacy_show = subparsers.add_parser("manifest-show", help="Show manifest summary (legacy)")
    legacy_show.add_argument("--path", type=Path, help="Optional manifest path")
    legacy_show.set_defaults(func=_cmd_manifest_show)

    legacy_verify = subparsers.add_parser("manifest-verify", help="Verify manifest digest (legacy)")
    legacy_verify.add_argument("--path", type=Path, help="Optional manifest path")
    legacy_verify.set_defaults(func=_cmd_manifest_verify)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="echo", description="Echo orchestration CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    _add_manifest_parsers(subparsers)
    provenance.build_parser(subparsers)
    policy_engine.build_parser(subparsers)
    graph.build_parser(subparsers)
    auto_release.build_parser(subparsers)
    akit_plan.build_parser(subparsers)

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if not hasattr(args, "func"):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover - script entry
    raise SystemExit(main())
