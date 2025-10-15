"""Echo command line entrypoints."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from tools import echo_manifest


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="echo", description="Echo toolkit CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    manifest_parser = subparsers.add_parser("manifest", help="Manage echo_manifest.json")
    manifest_subparsers = manifest_parser.add_subparsers(dest="manifest_command", required=True)

    for name in ("generate", "validate", "update"):
        sub = manifest_subparsers.add_parser(name, help=f"{name.title()} the manifest")
        sub.add_argument("--root", dest="root", default=None, help="Repository root")
        sub.add_argument("--manifest", dest="manifest", default=None, help="Manifest path")
        sub.add_argument("--schema", dest="schema", default=None, help="Schema path")
        if name == "generate":
            sub.add_argument(
                "--reuse-timestamp",
                action="store_true",
                default=False,
                help="Reuse generated_at if manifest content is unchanged",
            )
    return parser


def _resolve_root(root: str | None) -> Path:
    return Path(root or Path.cwd()).resolve()


def _resolve_manifest(root: Path, manifest: str | None) -> Path:
    return (root / (manifest or echo_manifest.DEFAULT_MANIFEST_PATH)).resolve()


def _resolve_schema(root: Path, schema: str | None) -> Path:
    return (root / (schema or echo_manifest.SCHEMA_PATH)).resolve()


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command != "manifest":
        parser.error("Unknown command")

    root = _resolve_root(getattr(args, "root", None))
    manifest_path = _resolve_manifest(root, getattr(args, "manifest", None))
    schema_path = _resolve_schema(root, getattr(args, "schema", None))

    try:
        if args.manifest_command == "generate":
            echo_manifest.generate_manifest(
                root,
                manifest_path,
                reuse_timestamp=getattr(args, "reuse_timestamp", False),
            )
        elif args.manifest_command == "validate":
            echo_manifest.validate_manifest(root, manifest_path, schema_path)
        elif args.manifest_command == "update":
            echo_manifest.update_manifest(root, manifest_path, schema_path)
        else:  # pragma: no cover - argparse guards this
            parser.error(f"Unknown manifest command: {args.manifest_command}")
    except Exception as exc:  # pragma: no cover - CLI error formatting
        parser.exit(1, f"{exc}\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
