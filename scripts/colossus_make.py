"""Colossus CLI entrypoint."""
from __future__ import annotations

from pathlib import Path
import argparse
import sys


DEFAULT_LAYOUT = [
    "colossus/logs",
    "colossus/data/seeds",
    "colossus/generate",
    "colossus/orchestrators",
    "colossus/verify",
    "colossus/explore/ui",
    "colossus/docs",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Colossus control CLI")
    parser.add_argument("--dry-run", action="store_true", help="show actions without executing")
    parser.add_argument("--out", type=Path, default=Path("."), help="override output root directory")
    parser.add_argument("--count", type=int, default=0, help="default artifact count hint")
    parser.add_argument("--seed", default=None, help="seed for deterministic operations")
    parser.add_argument("--resume-from", dest="resume_from", default=None, help="resume cycle index")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap_parser = subparsers.add_parser("bootstrap", help="prepare directory layout")
    bootstrap_parser.set_defaults(handler=bootstrap)

    for command in ("expand", "serve", "verify", "pack"):
        sub = subparsers.add_parser(command, help=f"{command} (planned in future PRs)")
        sub.set_defaults(handler=planned)

    return parser.parse_args(argv)


def bootstrap(args: argparse.Namespace) -> int:
    root = args.out
    actions = []
    for relative in DEFAULT_LAYOUT:
        target = root / relative
        actions.append(("mkdir", target))

    for action, path in actions:
        if args.dry_run:
            print(f"DRY-RUN {action}: {path}")
            continue
        path.mkdir(parents=True, exist_ok=True)
        if path.is_dir() and not any(path.iterdir()):
            keep = path / ".gitkeep"
            keep.touch(exist_ok=True)
        print(f"created {path}")
    return 0


def planned(args: argparse.Namespace) -> int:
    print(f"Command '{args.command}' will be implemented in a subsequent PR.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        raise RuntimeError("No handler resolved for command")
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
