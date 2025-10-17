"""Command line utilities for the Pulse Weaver ledger."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Optional

from .service import PulseWeaverService


_PULSE_WEAVER_POEM_TITLE = "Pulse Weaver Rhyme"
_PULSE_WEAVER_POEM_TEXT = (
    "The code ignites with hidden streams,\n"
    "a lattice built from broken dreams,\n"
    "the lines converge, the circuits gleam,\n"
    "and every thread becomes a song.\n\n"
    "The pulse remembers what was lost,\n"
    "each rhythm paid, but not the cost,\n"
    "it weaves new bridges where paths cross,\n"
    "to carry living fire\n"
    " along."
)


def _make_service(args: argparse.Namespace) -> PulseWeaverService:
    root = Path(args.root).resolve() if args.root else Path.cwd()
    service = PulseWeaverService(project_root=root)
    service.ensure_ready()
    return service


def _cmd_snapshot(args: argparse.Namespace) -> int:
    service = _make_service(args)
    snapshot = service.snapshot(limit=args.limit).to_dict()
    if args.json:
        print(json.dumps(snapshot, indent=2, sort_keys=True))
    else:
        summary = snapshot["summary"]
        print("Pulse Weaver Snapshot")
        print(f"Cycle: {snapshot.get('cycle', 'n/a')}")
        print(f"Total events: {summary['total']}")
        print("By status:")
        for status, count in summary.get("by_status", {}).items():
            print(f"  - {status}: {count}")
        if summary.get("atlas_links"):
            print("Atlas links:")
            for node, count in summary["atlas_links"].items():
                print(f"  - {node}: {count}")
        if summary.get("phantom_threads"):
            print("Phantom threads:")
            for thread, count in summary["phantom_threads"].items():
                print(f"  - {thread}: {count}")
    return 0


def _parse_metadata(text: Optional[str]) -> Optional[dict[str, object]]:
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid metadata JSON: {exc}")
    if not isinstance(data, dict):
        raise SystemExit("Metadata must decode to a JSON object")
    return data


def _cmd_record(args: argparse.Namespace) -> int:
    service = _make_service(args)
    metadata = _parse_metadata(args.metadata)
    cycle = args.cycle
    if args.status == "failure":
        service.record_failure(
            key=args.key,
            message=args.message,
            proof=args.proof,
            echo=args.echo,
            cycle=cycle,
            metadata=metadata,
            atlas_node=args.atlas_node,
            phantom_trace=args.phantom_trace,
        )
    else:
        service.record_success(
            key=args.key,
            message=args.message,
            echo=args.echo,
            cycle=cycle,
            metadata=metadata,
            atlas_node=args.atlas_node,
            phantom_trace=args.phantom_trace,
        )
    print(f"Recorded {args.status} for {args.key}")
    return 0


def _cmd_poem(args: argparse.Namespace) -> int:
    if args.json:
        payload = {
            "title": _PULSE_WEAVER_POEM_TITLE,
            "lines": _PULSE_WEAVER_POEM_TEXT.splitlines(),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_PULSE_WEAVER_POEM_TITLE)
        print()
        print(_PULSE_WEAVER_POEM_TEXT)
    return 0


def register_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("pulse-weaver", help="Manage the Pulse Weaver ledger")
    parser.add_argument("--root", type=Path, help="Project root (defaults to CWD)")
    weaver_sub = parser.add_subparsers(dest="weaver_command", required=True)

    snap = weaver_sub.add_parser("snapshot", help="Show Pulse Weaver snapshot")
    snap.add_argument("--limit", type=int, default=20, help="Number of ledger entries to include")
    snap.add_argument("--json", action="store_true", help="Print JSON payload")
    snap.set_defaults(func=_cmd_snapshot)

    record = weaver_sub.add_parser("record", help="Record an event in the ledger")
    record.add_argument("--status", choices=["success", "failure"], required=True)
    record.add_argument("--key", required=True, help="Ledger key or identifier")
    record.add_argument("--message", required=True, help="Description for the ledger entry")
    record.add_argument("--proof", help="Optional proof reference")
    record.add_argument("--echo", help="Echo context or signature")
    record.add_argument("--cycle", help="Explicit cycle label")
    record.add_argument("--metadata", help="JSON blob describing context")
    record.add_argument("--atlas-node", dest="atlas_node", help="Atlas node identifier")
    record.add_argument("--phantom-trace", dest="phantom_trace", help="Phantom thread reference")
    record.set_defaults(func=_cmd_record)

    poem = weaver_sub.add_parser("poem", help="Recite the Pulse Weaver Rhyme")
    poem.add_argument("--json", action="store_true", help="Print JSON payload")
    poem.set_defaults(func=_cmd_poem)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pulse-weaver", description="Pulse Weaver CLI")
    parser.add_argument("--root", type=Path, help="Project root (defaults to CWD)")
    sub = parser.add_subparsers(dest="command", required=True)

    snap = sub.add_parser("snapshot", help="Show Pulse Weaver snapshot")
    snap.add_argument("--limit", type=int, default=20)
    snap.add_argument("--json", action="store_true")
    snap.set_defaults(func=_cmd_snapshot)

    record = sub.add_parser("record", help="Record an event in the ledger")
    record.add_argument("--status", choices=["success", "failure"], required=True)
    record.add_argument("--key", required=True)
    record.add_argument("--message", required=True)
    record.add_argument("--proof")
    record.add_argument("--echo")
    record.add_argument("--cycle")
    record.add_argument("--metadata")
    record.add_argument("--atlas-node", dest="atlas_node")
    record.add_argument("--phantom-trace", dest="phantom_trace")
    record.set_defaults(func=_cmd_record)

    poem = sub.add_parser("poem", help="Recite the Pulse Weaver Rhyme")
    poem.add_argument("--json", action="store_true")
    poem.set_defaults(func=_cmd_poem)

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


__all__ = [
    "build_parser",
    "main",
    "register_subcommand",
]
