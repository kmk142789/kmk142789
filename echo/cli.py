"""Legacy compatibility CLI for the Echo project with manifest helpers."""

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


def _cmd_manifest_generate(args: argparse.Namespace) -> int:
    from tools.echo_manifest import generate_command

    generate_command(args.repo_root, args.output)
    return 0


def _cmd_manifest_validate(args: argparse.Namespace) -> int:
    from tools.echo_manifest import ManifestValidationError, validate_manifest

    try:
        validate_manifest(args.manifest, args.repo_root)
    except ManifestValidationError as exc:  # pragma: no cover - exercised in CLI tests
        print(str(exc))
        return 1
    return 0


def _cmd_manifest_update(args: argparse.Namespace) -> int:
    from tools.echo_manifest import ManifestValidationError, update_manifest

    try:
        update_manifest(args.manifest, args.repo_root)
    except ManifestValidationError as exc:  # pragma: no cover - exercised in CLI tests
        print(str(exc))
        return 1
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="echo",
        description="Echo compatibility CLI (delegates to echo.manifest_cli)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    refresh_parser = subparsers.add_parser("manifest-refresh", help="Refresh legacy manifest")
    refresh_parser.add_argument("--path", type=Path, help="Optional manifest path")
    refresh_parser.set_defaults(func=_cmd_refresh)

    show_parser = subparsers.add_parser("manifest-show", help="Show legacy manifest summary")
    show_parser.add_argument("--path", type=Path, help="Optional manifest path")
    show_parser.set_defaults(func=_cmd_show)

    verify_parser = subparsers.add_parser("manifest-verify", help="Verify legacy manifest digests")
    verify_parser.add_argument("--path", type=Path, help="Optional manifest path")
    verify_parser.set_defaults(func=_cmd_verify)

    manifest_parser = subparsers.add_parser("manifest", help="Manage the auto-maintained manifest")
    manifest_sub = manifest_parser.add_subparsers(dest="subcommand", required=True)

    manifest_generate = manifest_sub.add_parser("generate", help="Generate manifest snapshot")
    manifest_generate.add_argument("--repo-root", type=Path, help="Repository root", default=None)
    manifest_generate.add_argument("--output", type=Path, help="Manifest output path", default=None)
    manifest_generate.set_defaults(func=_cmd_manifest_generate)

    manifest_validate = manifest_sub.add_parser("validate", help="Validate manifest freshness")
    manifest_validate.add_argument("--repo-root", type=Path, help="Repository root", default=None)
    manifest_validate.add_argument("--manifest", type=Path, help="Manifest path", default=None)
    manifest_validate.set_defaults(func=_cmd_manifest_validate)

    manifest_update = manifest_sub.add_parser("update", help="Update manifest deterministically")
    manifest_update.add_argument("--repo-root", type=Path, help="Repository root", default=None)
    manifest_update.add_argument("--manifest", type=Path, help="Manifest path", default=None)
    manifest_update.set_defaults(func=_cmd_manifest_update)

    args = parser.parse_args(list(argv) if argv is not None else None)
    result = getattr(args, "func", None)
    if result is None:
        parser.print_help()
        return 1
    value = result(args)
    return int(value) if isinstance(value, int) else 0


if __name__ == "__main__":  # pragma: no cover - script entry
    raise SystemExit(main())
