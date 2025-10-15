"""Primary command line interface for Echo tooling."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from . import auto_release
from . import graph as graph_cli
from . import policy_engine, provenance
from akit import plan as akit_plan
from .manifest_cli import (
    load_manifest_ledger,
    manifest_status,
    refresh_manifest,
    verify_manifest,
    verify_manifest_ledger,
)


def _cmd_manifest_refresh(args: argparse.Namespace) -> int:
    refresh_manifest(args.path, ledger_path=args.ledger)
    return 0


def _cmd_manifest_verify(args: argparse.Namespace) -> int:
    manifest_ok = verify_manifest(args.path)
    ledger_ok = verify_manifest_ledger(
        manifest_path=args.path,
        ledger_path=args.ledger,
        require_gpg=args.require_gpg,
    )
    return 0 if manifest_ok and ledger_ok else 1


def _cmd_manifest_status(args: argparse.Namespace) -> int:
    status = manifest_status(args.path, args.ledger)
    latest = status["latest_entry"]
    print(f"Manifest: {status['manifest_path']}")
    print(f"Ledger:   {status['ledger_path']}")
    print(f"Ledger entries: {status['ledger_entries']}")
    if latest:
        print(f"Latest digest: {latest['manifest_digest']}")
        print(f"Latest commit: {latest['commit']}")
        print(f"Ledger seal:  {latest['ledger_seal']}")
    else:
        print("Ledger empty")
    if status["ledger_match"]:
        print("Manifest digest matches latest ledger entry")
        return 0
    print("Manifest digest does not match ledger entry")
    return 1


def _cmd_manifest_ledger(args: argparse.Namespace) -> int:
    entries = load_manifest_ledger(args.ledger)
    to_show = entries if args.limit == 0 else entries[-args.limit :]
    for entry in to_show:
        print(json.dumps(entry, sort_keys=True))
    if args.verify:
        ok = verify_manifest_ledger(
            manifest_path=args.path,
            ledger_path=args.ledger,
            require_gpg=args.require_gpg,
        )
        return 0 if ok else 1
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="echo", description="Echo command line interface")
    subparsers = parser.add_subparsers(dest="command", required=True)

    refresh_parser = subparsers.add_parser(
        "manifest-refresh", help="Regenerate the manifest and append a ledger entry"
    )
    refresh_parser.add_argument("--path", type=Path, help="Optional manifest output path")
    refresh_parser.add_argument("--ledger", type=Path, help="Optional ledger override")
    refresh_parser.set_defaults(func=_cmd_manifest_refresh)

    verify_parser = subparsers.add_parser(
        "manifest-verify", help="Verify manifest integrity and ledger seals"
    )
    verify_parser.add_argument("--path", type=Path, help="Optional manifest path")
    verify_parser.add_argument("--ledger", type=Path, help="Optional ledger path")
    verify_parser.add_argument(
        "--require-gpg",
        action="store_true",
        help="Require commit signature verification",
    )
    verify_parser.set_defaults(func=_cmd_manifest_verify)

    status_parser = subparsers.add_parser(
        "manifest-status", help="Display manifest and ledger status"
    )
    status_parser.add_argument("--path", type=Path, help="Optional manifest path")
    status_parser.add_argument("--ledger", type=Path, help="Optional ledger path")
    status_parser.set_defaults(func=_cmd_manifest_status)

    ledger_parser = subparsers.add_parser(
        "manifest-ledger", help="Inspect manifest ledger history"
    )
    ledger_parser.add_argument("--path", type=Path, help="Optional manifest path")
    ledger_parser.add_argument("--ledger", type=Path, help="Optional ledger path")
    ledger_parser.add_argument(
        "--limit", type=int, default=10, help="Number of entries to display (0 for all)"
    )
    ledger_parser.add_argument(
        "--verify", action="store_true", help="Verify ledger integrity and seals"
    )
    ledger_parser.add_argument(
        "--require-gpg",
        action="store_true",
        help="Require commit signature verification when using --verify",
    )
    ledger_parser.set_defaults(func=_cmd_manifest_ledger)

    provenance.build_parser(subparsers)
    policy_engine.build_parser(subparsers)
    graph_cli.build_parser(subparsers)
    akit_plan.build_parser(subparsers)
    auto_release.build_parser(subparsers)

    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover - script entry
    raise SystemExit(main())
