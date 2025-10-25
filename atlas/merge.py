"""Command line interface for merging universes."""

from __future__ import annotations

from pathlib import Path
import argparse

from .graph import FederationGraph
from .resolver import merge_universes, save_merge


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Merge universes into a canonical stream")
    parser.add_argument("--graph", type=Path, default=Path("build/atlas/global_graph.json"), help="Global graph path")
    parser.add_argument("--universe", nargs="+", required=True, help="Universe identifiers to merge")
    parser.add_argument("--policy", default="latest-wins", help="Merge policy")
    parser.add_argument("--out", type=Path, required=True, help="Destination directory")
    args = parser.parse_args(argv)

    graph = FederationGraph.load(args.graph)
    result = merge_universes(graph, args.universe, policy=args.policy)
    save_merge(result, args.out)
    print(
        f"Merged {len(result['artifacts'])} artifacts from {', '.join(args.universe)} "
        f"using policy {args.policy} -> {args.out}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
