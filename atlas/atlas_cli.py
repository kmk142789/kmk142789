"""Unified CLI entry point for Atlas operations."""

from __future__ import annotations

from pathlib import Path
import argparse

from . import dedupe, explore, federation, merge, search


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Atlas cross-universe federation toolkit")
    sub = parser.add_subparsers(dest="command", required=True)

    fed_parser = sub.add_parser("federate", help="Build the global federation graph")
    fed_parser.add_argument("--cosmos", type=Path, required=True)
    fed_parser.add_argument("--fractals", type=Path, required=True)
    fed_parser.add_argument("--out", type=Path, required=True)

    dedupe_parser = sub.add_parser("dedupe", help="Run federation dedupe")
    dedupe_parser.add_argument("--graph", type=Path, required=True)
    dedupe_parser.add_argument("--out", type=Path, required=True)
    dedupe_parser.add_argument("--search-index", type=Path)

    explore_parser = sub.add_parser("explore", help="Explore the global graph")
    explore_parser.add_argument("--graph", type=Path, required=True)
    explore_parser.add_argument("--universe")
    explore_parser.add_argument("--artifact")

    search_parser = sub.add_parser("search", help="Query the federated index")
    search_parser.add_argument("--index", type=Path, required=True)
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--limit", type=int, default=10)
    search_parser.add_argument("--cycle", type=int)
    search_parser.add_argument("--puzzle", type=int)
    search_parser.add_argument("--address")

    merge_parser = sub.add_parser("merge", help="Merge universes into a canonical stream")
    merge_parser.add_argument("--graph", type=Path, default=Path("build/atlas/global_graph.json"))
    merge_parser.add_argument("--universe", nargs="+", required=True)
    merge_parser.add_argument("--policy", default="latest-wins")
    merge_parser.add_argument("--out", type=Path, required=True)

    args = parser.parse_args(argv)

    if args.command == "federate":
        return federation.main([
            "--cosmos",
            str(args.cosmos),
            "--fractals",
            str(args.fractals),
            "--out",
            str(args.out),
        ])
    if args.command == "dedupe":
        cli_args = ["--graph", str(args.graph), "--out", str(args.out)]
        if args.search_index:
            cli_args.extend(["--search-index", str(args.search_index)])
        return dedupe.main(cli_args)
    if args.command == "explore":
        cli_args = ["--graph", str(args.graph)]
        if args.universe:
            cli_args.extend(["--universe", args.universe])
        if args.artifact:
            cli_args.extend(["--artifact", args.artifact])
        return explore.main(cli_args)
    if args.command == "search":
        cli_args = ["--index", str(args.index), "--query", args.query, "--limit", str(args.limit)]
        if args.cycle is not None:
            cli_args.extend(["--cycle", str(args.cycle)])
        if args.puzzle is not None:
            cli_args.extend(["--puzzle", str(args.puzzle)])
        if args.address:
            cli_args.extend(["--address", args.address])
        return search.main(cli_args)
    if args.command == "merge":
        cli_args = [
            "--graph",
            str(args.graph),
            "--universe",
            *args.universe,
            "--policy",
            args.policy,
            "--out",
            str(args.out),
        ]
        return merge.main(cli_args)
    raise RuntimeError("Unknown command")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
