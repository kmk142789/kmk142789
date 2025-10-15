"""Primary Echo command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from . import manifest as manifest_module


def _manifest_command(args: argparse.Namespace) -> int:
    action = args.action
    manifest_path = Path(args.manifest).expanduser() if args.manifest else manifest_module.DEFAULT_MANIFEST_PATH
    root = Path(args.root).expanduser() if args.root else manifest_module.REPO_ROOT

    if action == "refresh":
        manifest_module.refresh_manifest(root=root, manifest_path=manifest_path)
        return 0
    if action == "show":
        output = manifest_module.show_manifest(manifest_path=manifest_path)
        sys.stdout.write(output)
        return 0
    if action == "verify":
        try:
            manifest_module.verify_manifest(root=root, manifest_path=manifest_path)
            return 0
        except manifest_module.ManifestDriftError as exc:
            for mismatch in exc.mismatches:
                sys.stderr.write(f"drift detected: {mismatch}\n")
            return 1
    raise manifest_module.ManifestError(f"Unsupported manifest action: {action}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="echo", description="Echo orchestration toolkit")
    parser.add_argument("--root", help="Override repository root", default=None)
    parser.add_argument(
        "--manifest",
        help="Path to the manifest file (default: echo_manifest.json)",
        default=None,
    )

    subparsers = parser.add_subparsers(dest="command")
    manifest_parser = subparsers.add_parser("manifest", help="Manage Echo manifest records")
    manifest_parser.add_argument("action", choices=["refresh", "show", "verify"], help="Manifest action")
    manifest_parser.set_defaults(func=_manifest_command)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())

