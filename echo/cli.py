"""Primary command line interface for Echo tooling."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

from .manifest_cli import (
    load_manifest_ledger,
    manifest_status,
    refresh_manifest,
    verify_manifest,
    verify_manifest_ledger,
)
from . import provenance


def _cmd_provenance_emit(args: argparse.Namespace) -> int:
    context = args.context
    if context.startswith("engine:") and not args.cycle_id:
        cycle_id = context.split(":", 1)[1]
    else:
        cycle_id = args.cycle_id
    try:
        provenance.emit(
            context=context,
            inputs=[Path(p) for p in args.inputs],
            outputs=[Path(p) for p in args.outputs],
            cycle_id=cycle_id,
            runtime_seed=args.runtime_seed,
            actor=args.actor,
            manifest_path=args.manifest,
            output_path=args.output,
            sign=args.gpg_sign,
            gpg_key=args.gpg_key,
        )
    except provenance.ProvenanceError as error:
        print(f"provenance emit failed: {error}", file=sys.stderr)
        return 2
    return 0


def _cmd_provenance_verify(args: argparse.Namespace) -> int:
    try:
        record = provenance.verify(args.path, require_signature=args.require_signature)
    except provenance.ProvenanceError as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(record.to_dict(), indent=2, sort_keys=True))
    return 0


def _cmd_provenance_bundle(args: argparse.Namespace) -> int:
    try:
        bundle_path = provenance.bundle(
            source=args.source,
            output=args.output,
            include_hidden=args.include_hidden,
        )
    except provenance.ProvenanceError as error:
        print(str(error), file=sys.stderr)
        return 2
    print(bundle_path)
    return 0


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

    provenance_parser = subparsers.add_parser("provenance", help="Provenance management")
    provenance_sub = provenance_parser.add_subparsers(dest="provenance_command", required=True)

    emit_parser = provenance_sub.add_parser("emit", help="Emit provenance record")
    emit_parser.add_argument("--context", required=True, help="Execution context (manifest or engine:NAME)")
    emit_parser.add_argument("--input", dest="inputs", action="append", default=[], help="Input file path")
    emit_parser.add_argument(
        "--output-file",
        dest="outputs",
        action="append",
        default=[],
        help="Output artifact path",
    )
    emit_parser.add_argument("--manifest", type=Path, help="Override manifest path")
    emit_parser.add_argument("--cycle-id", help="Override cycle identifier")
    emit_parser.add_argument("--runtime-seed", help="Optional runtime seed")
    emit_parser.add_argument("--actor", help="Actor responsible for the run")
    emit_parser.add_argument("--output", type=Path, help="Where to write provenance JSON")
    emit_parser.add_argument("--gpg-sign", action="store_true", help="Sign using GPG")
    emit_parser.add_argument("--gpg-key", help="GPG key identifier when signing")
    emit_parser.set_defaults(func=_cmd_provenance_emit)

    verify_parser = provenance_sub.add_parser("verify", help="Verify provenance seal and signature")
    verify_parser.add_argument("path", type=Path, help="Path to provenance JSON")
    verify_parser.add_argument(
        "--require-signature",
        action="store_true",
        help="Require GPG signature verification",
    )
    verify_parser.set_defaults(func=_cmd_provenance_verify)

    bundle_parser = provenance_sub.add_parser("bundle", help="Bundle provenance artifacts")
    bundle_parser.add_argument("--source", type=Path, help="Directory containing provenance JSON")
    bundle_parser.add_argument("--output", type=Path, help="Target tar.gz path")
    bundle_parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files in the bundle",
    )
    bundle_parser.set_defaults(func=_cmd_provenance_bundle)

    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover - script entry
    raise SystemExit(main())
