"""Echo command line interface shim."""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from tools import echo_manifest


def _build_manifest_parser(subparsers: argparse._SubParsersAction) -> None:
    manifest_parser = subparsers.add_parser("manifest", help="Interact with the echo manifest")
    manifest_sub = manifest_parser.add_subparsers(dest="manifest_command")

    gen_parser = manifest_sub.add_parser("generate", help="Generate the manifest")
    gen_parser.add_argument("--repo", help="Path to the repository root")
    gen_parser.add_argument("--output", help="Path to write the manifest")
    gen_parser.set_defaults(func=lambda ns: echo_manifest.generate_command(ns))

    val_parser = manifest_sub.add_parser("validate", help="Validate the manifest")
    val_parser.add_argument("--repo", help="Path to the repository root")
    val_parser.add_argument("--manifest", help="Path to the manifest file")
    val_parser.set_defaults(func=lambda ns: echo_manifest.validate_command(ns))

    upd_parser = manifest_sub.add_parser("update", help="Update the manifest in place")
    upd_parser.add_argument("--repo", help="Path to the repository root")
    upd_parser.add_argument("--manifest", help="Path to the manifest file")
    upd_parser.set_defaults(func=lambda ns: echo_manifest.update_command(ns))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Echo CLI")
    subparsers = parser.add_subparsers(dest="command")
    _build_manifest_parser(subparsers)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover - CLI entry
    sys.exit(main())
