"""CLI entry point for compiling Singularity logs into Dominion plans."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from .plans import DominionPlan, intents_from_log, load_log


def _compile_command(args: argparse.Namespace) -> None:
    source = Path(args.source)
    out_dir = Path(args.out)
    name: Optional[str] = args.name

    if not source.exists():
        raise SystemExit(f"Singularity log not found: {source}")

    events = load_log(source)
    intents = intents_from_log(events)
    plan = DominionPlan.from_intents(intents, source=str(source))

    filename = name or f"plan_{plan.plan_id}.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    plan.write(path)
    print(f"Plan {plan.plan_id} written to {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compile Singularity action intents into Dominion plans.")
    subparsers = parser.add_subparsers(dest="command")

    compile_parser = subparsers.add_parser("compile", help="Compile a plan from a log file.")
    compile_parser.add_argument("--from", dest="source", required=True, help="Path to singularity log JSON.")
    compile_parser.add_argument(
        "--out",
        dest="out",
        default="build/dominion/plans",
        help="Directory for compiled plans.",
    )
    compile_parser.add_argument("--name", dest="name", help="Explicit plan filename.")
    compile_parser.set_defaults(func=_compile_command)
    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
