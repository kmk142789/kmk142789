"""Generate the puzzle lineage graph artifacts."""
from __future__ import annotations

import argparse
import json
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

from puzzle_data import build_lookup, lineage_links, load_puzzles


USAGE = """\
Echo Expansion — Puzzle Lineage Generator
=========================================
This tool builds the lineage graph data (JSON + DOT + PNG) for the puzzle
ecosystem.  Usage examples:

  python scripts/generate_lineage.py
  python scripts/generate_lineage.py --index data/puzzle_index.json --output build/lineage
"""


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def build_domain_edges(domain_map: Dict[str, Dict[str, object]], lookup: Dict[int, object]) -> List[Dict[str, object]]:
    domain_to_ids: Dict[str, List[int]] = defaultdict(list)
    address_to_id = {puzzle.address: puzzle.id for puzzle in lookup.values()}
    for address, payload in domain_map.items():
        domains = payload.get("domains") if isinstance(payload, dict) else None
        if not isinstance(domains, list):
            continue
        for domain in domains:
            if not isinstance(domain, str):
                continue
            puzzle_id = address_to_id.get(address)
            if puzzle_id:
                domain_to_ids[domain].append(puzzle_id)
    edges: List[Dict[str, object]] = []
    for domain, ids in domain_to_ids.items():
        unique_ids = sorted(set(ids))
        if len(unique_ids) < 2:
            continue
        for i, source in enumerate(unique_ids):
            for target in unique_ids[i + 1 :]:
                edges.append({"source": source, "target": target, "domain": domain, "kind": "domain"})
    return edges


def load_domain_map(path: Path) -> Dict[str, Dict[str, object]]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError:
        return {}
    domains = payload.get("domains")
    if isinstance(domains, dict):
        return domains  # expected format {address: {...}}
    return {}


def compose_dot(nodes: Iterable[object], edges: List[Dict[str, object]]) -> str:
    lines = [
        "digraph PuzzleLineage {",
        "  rankdir=LR;",
        "  node [shape=record, style=filled, fillcolor=\"#0b3d91\", fontcolor=white, fontname=Helvetica];",
    ]
    for node in nodes:
        label = f"Puzzle {node.id}\\n{node.address}\\n{node.script_type.upper()}"
        status_color = {
            "reconstructed": "#0b3d91",
            "missing": "#9b1b30",
            "in-progress": "#f08a24",
        }.get(node.status, "#0b3d91")
        lines.append(
            f"  n{node.id} [label=\"{label}\", fillcolor=\"{status_color}\"];"
        )
    for edge in edges:
        label = edge.get("domain") or edge.get("hash160") or edge.get("pubkey") or "link"
        lines.append(f"  n{edge['source']} -> n{edge['target']} [label=\"{label}\"];")
    lines.append("}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the puzzle lineage graph artifacts.")
    parser.add_argument("--index", type=Path, default=None, help="Path to the puzzle index JSON file.")
    parser.add_argument("--output", type=Path, default=Path("build/lineage"), help="Directory for generated artifacts.")
    parser.add_argument("--domain-map", type=Path, default=Path("build/domains/map.json"), help="Optional domain enrichment map.")
    parser.add_argument("--no-png", action="store_true", help="Skip the Graphviz PNG rendering step.")
    args = parser.parse_args()

    print(USAGE)

    puzzles = load_puzzles(args.index)
    lookup = build_lookup(puzzles)
    base_edges: List[Dict[str, object]] = lineage_links(args.index)

    domain_edges = build_domain_edges(load_domain_map(args.domain_map), lookup)
    all_edges = base_edges + domain_edges

    output_dir = args.output
    ensure_directory(output_dir)

    json_payload = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "nodes": [
            {
                "id": puzzle.id,
                "title": puzzle.title,
                "script_type": puzzle.script_type,
                "address": puzzle.address,
                "status": puzzle.status,
            }
            for puzzle in puzzles
        ],
        "edges": all_edges,
        "stats": {
            "node_count": len(puzzles),
            "edge_count": len(all_edges),
            "source": str(args.index or "data/puzzle_index.json"),
        },
    }

    json_path = output_dir / "lineage.json"
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(json_payload, handle, indent=2)
        handle.write("\n")
    print(f"[lineage] JSON summary written to {json_path}")

    dot_path = output_dir / "lineage.dot"
    dot_source = compose_dot(puzzles, all_edges)
    dot_path.write_text(dot_source, encoding="utf-8")
    print(f"[lineage] DOT graph written to {dot_path}")

    if not args.no_png:
        png_path = output_dir / "lineage.png"
        try:
            completed = subprocess.run(
                ["dot", "-Tpng", str(dot_path), "-o", str(png_path)],
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            print("[lineage] Graphviz 'dot' executable not available; skipped PNG rendering.")
        else:
            if completed.returncode == 0:
                print(f"[lineage] PNG rendering complete: {png_path}")
            else:
                print("[lineage] dot exited with a non-zero status; stderr follows:")
                print(completed.stderr)
    else:
        print("[lineage] PNG rendering explicitly disabled via --no-png.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
