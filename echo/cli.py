"""Legacy compatibility CLI for the Echo project.

The primary command entry point for the ``echo`` console script now lives in
``echo.manifest_cli``.  This shim keeps the old module importable while
delegating to the new implementation.  It exposes a reduced set of commands
that mirror the previous behaviour but rely on the modern manifest helpers.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

from .manifest_cli import refresh_manifest, show_manifest, verify_manifest
from .shard_vault import ingest_shard_text


def _cmd_refresh(args: argparse.Namespace) -> int:
    refresh_manifest(args.path)
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    show_manifest(args.path)
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    return 0 if verify_manifest(args.path) else 1


def _cmd_ingest_shard(args: argparse.Namespace) -> int:
    if not args.from_stdin and args.from_file is None:
        raise SystemExit("provide --from-file or --from-stdin")
    if args.from_stdin and args.from_file is not None:
        raise SystemExit("choose either --from-file or --from-stdin")

    if args.from_stdin:
        text = sys.stdin.read()
    else:
        text = Path(args.from_file).read_text(encoding="utf-8")

    result = ingest_shard_text(
        text,
        shards_root=args.shards_root,
        manifest_path=args.manifest_path,
    )
    print(
        f"saved {result['bin_path']} {result['attestation_path']} (txid {result['txid']})"
    )
    return 0


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

    ingest_parser = subparsers.add_parser(
        "ingest-shard", help="Ingest an ECHO shard vault blob"
    )
    ingest_parser.add_argument("--from-file", type=Path, help="path to blob text")
    ingest_parser.add_argument(
        "--from-stdin", action="store_true", help="read blob contents from stdin"
    )
    ingest_parser.add_argument(
        "--shards-root", type=Path, default=Path("vault/shards"), help="output directory"
    )
    ingest_parser.add_argument(
        "--manifest-path",
        type=Path,
        default=Path("echo_manifest.json"),
        help="manifest file to update",
    )
    ingest_parser.set_defaults(func=_cmd_ingest_shard)

    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover - script entry
    raise SystemExit(main())
