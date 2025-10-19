"""Impact graph construction and forecasting utilities."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from ._paths import REPO_ROOT

_DEFAULT_MANIFEST = REPO_ROOT / "echo_manifest.json"


@dataclass
class ImpactGraph:
    nodes: Dict[str, dict]
    edges: Set[Tuple[str, str]]
    digest: str

    def to_table(self) -> str:
        lines = ["SOURCE\tTARGET"]
        for source, target in sorted(self.edges):
            lines.append(f"{source}\t{target}")
        return "\n".join(lines)

    def to_dot(self) -> str:
        lines = ["digraph echo {"]
        for node in sorted(self.nodes):
            lines.append(f'  "{node}";')
        for source, target in sorted(self.edges):
            lines.append(f'  "{source}" -> "{target}";')
        lines.append("}")
        return "\n".join(lines)

    def impacted_nodes(self, paths: Iterable[str]) -> Set[str]:
        impacted: Set[str] = set()
        path_set = set(paths)
        for node, meta in self.nodes.items():
            spec = meta.get("module_spec") or meta.get("path")
            if not spec:
                continue
            module_path = spec.split(":")[0].replace(".", "/") + ".py"
            if module_path in path_set:
                impacted.add(node)
                impacted.update(self._neighbors(node))
        return impacted

    def _neighbors(self, node: str) -> Set[str]:
        connected = {target for source, target in self.edges if source == node}
        connected.update({source for source, target in self.edges if target == node})
        return connected


def _canonical_digest(edges: Iterable[Tuple[str, str]]) -> str:
    import hashlib

    payload = "|".join(f"{a}->{b}" for a, b in sorted(edges))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_graph(manifest: Optional[dict] = None, manifest_path: Path | None = None) -> ImpactGraph:
    if manifest is None:
        manifest_path = manifest_path or _DEFAULT_MANIFEST
        if not manifest_path.exists():
            raise FileNotFoundError(manifest_path)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    nodes: Dict[str, dict] = {"manifest": {"type": "root"}}
    edges: Set[Tuple[str, str]] = set()
    for category in ("engines", "states", "assistant_kits"):
        for entry in manifest.get(category, []):
            node_id = f"{category}:{entry['name']}"
            nodes[node_id] = entry
            edges.add(("manifest", node_id))
    digest = _canonical_digest(edges)
    return ImpactGraph(nodes=nodes, edges=edges, digest=digest)


def forecast_resonance(graph: ImpactGraph, window: str = "7d") -> Dict[str, float]:
    try:
        window_days = int(window.rstrip("d"))
    except ValueError:
        window_days = 7
    base = max(1, len(graph.nodes) - 1)
    results: Dict[str, float] = {}
    for node in graph.nodes:
        degree = len(graph._neighbors(node))
        score = degree / base
        decay = math.exp(-window_days / 30)
        results[node] = round(score * (1 + decay), 4)
    return results


def _cmd_show(args: argparse.Namespace) -> int:
    graph = build_graph()
    if args.as_format == "dot":
        print(graph.to_dot())
    else:
        print(graph.to_table())
    return 0


def _cmd_impact(args: argparse.Namespace) -> int:
    graph = build_graph()
    impacted = graph.impacted_nodes(args.paths)
    print(json.dumps(sorted(impacted), indent=2))
    return 0


def _cmd_forecast(args: argparse.Namespace) -> int:
    graph = build_graph()
    forecast = forecast_resonance(graph, window=args.window)
    print(json.dumps(forecast, indent=2))
    return 0


def build_parser(subparsers: argparse._SubParsersAction) -> None:
    graph_parser = subparsers.add_parser("graph", help="Impact graph utilities")
    graph_parser.add_argument("--as", dest="as_format", choices=["table", "dot"], default="table")
    graph_parser.set_defaults(func=_cmd_show)

    impact_parser = subparsers.add_parser("impact", help="Show impacted graph nodes")
    impact_parser.add_argument("paths", nargs="+", help="Changed file paths")
    impact_parser.set_defaults(func=_cmd_impact)

    forecast_parser = subparsers.add_parser("forecast", help="Forecast resonance")
    forecast_parser.add_argument("--window", default="7d")
    forecast_parser.set_defaults(func=_cmd_forecast)


__all__ = ["ImpactGraph", "build_graph", "forecast_resonance", "build_parser"]

