"""Interactive exploration helpers for the Atlas graph."""

from __future__ import annotations

from pathlib import Path
import argparse
import json

from .graph import FederationGraph


def _print_universe(graph: FederationGraph, universe: str) -> None:
    nodes = list(graph.iter_universe(universe))
    print(f"Universe {universe}: {len(nodes)} artifacts")
    for node in nodes:
        deps = ", ".join(node.dependencies) if node.dependencies else "<none>"
        print(f"  - {node.node_id} [{node.source}] deps=({deps})")


def _print_artifact(graph: FederationGraph, node_id: str) -> None:
    mapping = graph.artifact_map()
    node = mapping.get(node_id)
    if not node:
        print(f"Artifact {node_id} not found")
        return
    print(json.dumps(node.to_dict(), indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Explore the Atlas federation graph")
    parser.add_argument("--graph", type=Path, required=True, help="Path to global graph JSON")
    parser.add_argument("--universe", help="Universe identifier to inspect")
    parser.add_argument("--artifact", help="Specific artifact node id to inspect")
    args = parser.parse_args(argv)

    graph = FederationGraph.load(args.graph)
    if args.universe:
        _print_universe(graph, args.universe)
    if args.artifact:
        _print_artifact(graph, args.artifact)
    if not args.universe and not args.artifact:
        print("Available universes:")
        for universe, info in sorted(graph.universes.items()):
            print(
                f"- {universe}: {info.get('artifact_count', 0)} artifacts from {', '.join(info.get('sources', []))}"
            )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
