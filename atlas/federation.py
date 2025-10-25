"""Builds the global Atlas federation graph by stitching cosmos and fractal shards."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List
import argparse
import json

from .graph import ArtifactNode, Edge, FederationGraph


@dataclass(slots=True)
class _UniverseInput:
    universe: str
    source: str
    payload: Dict


def _iter_payloads(root: Path, source: str) -> Iterator[_UniverseInput]:
    for path in sorted(root.glob("*.json")):
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        universe = data.get("universe")
        if not universe:
            raise ValueError(f"File {path} is missing required 'universe' field")
        yield _UniverseInput(universe=universe, source=source, payload=data)


def _normalise_dependency(raw: str, default_universe: str) -> str:
    if "::" in raw:
        return raw
    if ":" in raw:
        universe, artifact_id = raw.split(":", 1)
        return f"{universe}::{artifact_id}"
    return f"{default_universe}::{raw}"


def _normalise_artifacts(inputs: Iterable[_UniverseInput]) -> tuple[list[ArtifactNode], list[Edge], dict[str, dict]]:
    artifacts: List[ArtifactNode] = []
    edges: List[Edge] = []
    universes: Dict[str, Dict] = defaultdict(lambda: {"sources": set(), "artifact_count": 0})

    for universe_input in inputs:
        universe = universe_input.universe
        universes[universe]["sources"].add(universe_input.source)
        shard_artifacts = universe_input.payload.get("artifacts", [])
        for shard_artifact in shard_artifacts:
            artifact_id = shard_artifact.get("id")
            if not artifact_id:
                raise ValueError(f"Artifact in universe {universe} missing 'id'")
            node_id = f"{universe}::{artifact_id}"
            metadata = shard_artifact.get("metadata", {})
            content = shard_artifact.get("content", "")
            dependencies = [
                _normalise_dependency(dep, universe)
                for dep in shard_artifact.get("dependencies", [])
            ]
            timestamp = shard_artifact.get("timestamp") or universe_input.payload.get("generated_at")
            artifacts.append(
                ArtifactNode(
                    node_id=node_id,
                    universe=universe,
                    artifact_id=artifact_id,
                    source=universe_input.source,
                    metadata=metadata,
                    content=content,
                    dependencies=dependencies,
                    timestamp=timestamp,
                )
            )
            universes[universe]["artifact_count"] += 1
            for dependency in dependencies:
                edges.append(Edge(source=node_id, target=dependency))
    # serialise sources back to list
    for universe, payload in universes.items():
        payload["sources"] = sorted(payload["sources"])
    return artifacts, edges, dict(universes)


def build_global_graph(cosmos_root: Path, fractal_root: Path) -> FederationGraph:
    """Return a :class:`FederationGraph` generated from shard outputs."""

    cosmos_inputs = list(_iter_payloads(cosmos_root, "cosmos")) if cosmos_root.exists() else []
    fractal_inputs = list(_iter_payloads(fractal_root, "fractal")) if fractal_root.exists() else []
    inputs = cosmos_inputs + fractal_inputs
    if not inputs:
        raise FileNotFoundError("No cosmos or fractal payloads were discovered")

    artifacts, edges, universes = _normalise_artifacts(inputs)
    # filter edges to those referencing known nodes
    known_nodes = {artifact.node_id for artifact in artifacts}
    edges = [edge for edge in edges if edge.target in known_nodes]

    # update universe metadata with sorted edges count
    for universe in universes:
        universes[universe]["edge_count"] = sum(
            1 for edge in edges if edge.source.startswith(f"{universe}::")
        )

    return FederationGraph(universes=universes, artifacts=artifacts, edges=edges)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the global Atlas federation graph")
    parser.add_argument("--cosmos", type=Path, required=True, help="Directory containing cosmos outputs")
    parser.add_argument("--fractals", type=Path, required=True, help="Directory containing fractal outputs")
    parser.add_argument("--out", type=Path, required=True, help="Destination for the global graph JSON")
    args = parser.parse_args(argv)

    graph = build_global_graph(args.cosmos, args.fractals)
    graph.save(args.out)
    print(
        f"Global federation graph with {len(graph.artifacts)} artifacts and {len(graph.edges)} edges "
        f"written to {args.out}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
