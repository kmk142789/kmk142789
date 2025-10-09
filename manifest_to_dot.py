#!/usr/bin/env python3
"""Generate a Graphviz DOT graph from ``out_manifest.json``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set, Tuple
from urllib.parse import urlparse

DEFAULT_INPUT = Path("out_manifest.json")
DEFAULT_OUTPUT = Path("echo_network.dot")

REPO_STYLE = {
    "shape": "box",
    "style": "filled",
    "fillcolor": "#101820",
    "fontcolor": "#ffffff",
    "fontsize": "10",
}

TOPIC_STYLE = {
    "shape": "oval",
    "style": "filled",
    "fillcolor": "#2b6f9b",
    "fontcolor": "#ffffff",
    "fontsize": "9",
}

GRAPH_STYLE = {
    "rankdir": "LR",
    "splines": "true",
    "overlap": "false",
    "bgcolor": "#0b0f14",
}

NODE_FONT = "Helvetica"
MAX_TOPICS_PER_REPO = 6


class ManifestError(RuntimeError):
    """Raised when the manifest file cannot be processed."""


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to the manifest JSON file (default: out_manifest.json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Destination DOT file (default: echo_network.dot)",
    )
    parser.add_argument(
        "--max-topics",
        type=int,
        default=MAX_TOPICS_PER_REPO,
        help="Maximum number of topics to link per repository (default: 6)",
    )
    return parser.parse_args(argv)


def load_manifest(path: Path) -> Sequence[dict]:
    if not path.exists():
        raise ManifestError(f"{path} not found. Run the manifest script first.")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"Failed to parse {path}: {exc}") from exc

    if not isinstance(data, list):
        raise ManifestError("Manifest root must be a list of repository entries")

    return data


def safe_label(value: str) -> str:
    """Return a DOT-safe label with conservative truncation."""

    escaped = value.replace("\"", r"\"")
    # The DOT format copes poorly with very long labels. 140 characters keeps the
    # graph readable without losing too much context.
    return escaped[:140]


def normalise_topics(raw_topics: object) -> List[str]:
    if raw_topics is None:
        return []
    if isinstance(raw_topics, list):
        return [str(t).strip() for t in raw_topics if str(t).strip()]
    if isinstance(raw_topics, str):
        return [t.strip() for t in raw_topics.split(",") if t.strip()]
    return []


def build_graph(
    manifest: Sequence[dict],
    max_topics: int,
) -> Tuple[Set[str], Set[str]]:
    nodes: Set[str] = set()
    edges: Set[str] = set()

    for entry in manifest:
        if not isinstance(entry, dict):
            continue

        name_fields = (
            entry.get("repo_name"),
            entry.get("full_name"),
            entry.get("repo_path"),
        )

        repo_name: Optional[str] = None
        for field in name_fields:
            if not isinstance(field, str):
                continue
            candidate = field.strip()
            if not candidate:
                continue
            # ``repo_path`` can be a filesystem path; ``full_name`` normally uses
            # the ``owner/name`` GitHub notation.  Fall back to the basename when
            # the field looks like a path, otherwise keep the raw identifier.
            if candidate.startswith("http"):
                # ``html_url`` style field; keep the final path component which is
                # the repository slug on GitHub ("owner/repo").
                parsed = urlparse(candidate)
                parts = [p for p in parsed.path.strip("/").split("/") if p]
                repo_name = "/".join(parts[-2:]) if parts else parsed.netloc or candidate
            elif candidate.startswith("/") or candidate.startswith(".") or "\\" in candidate:
                repo_name = Path(candidate).name
            elif candidate.count("/") == 1:
                repo_name = candidate
            else:
                repo_name = candidate
            break
        if not repo_name:
            continue

        repo_label = safe_label(repo_name)
        nodes.add(render_node(repo_label, REPO_STYLE))

        topics = normalise_topics(entry.get("topics"))[:max_topics]
        for topic in topics:
            topic_label = safe_label(topic)
            nodes.add(render_node(topic_label, TOPIC_STYLE))
            edges.add(render_edge(repo_label, topic_label))

    return nodes, edges


def render_attrs(attrs: dict) -> str:
    return " " + " ".join(f'{key}="{value}"' for key, value in attrs.items()) if attrs else ""


def render_node(label: str, attrs: dict) -> str:
    return f'  "{label}"{render_attrs(attrs)};'


def render_edge(src: str, dst: str) -> str:
    return f'  "{src}" -> "{dst}";'


def render_graph(nodes: Iterable[str], edges: Iterable[str]) -> str:
    header = ["digraph EchoNetwork {"]
    graph_attrs = " ".join(f'{k}="{v}"' for k, v in GRAPH_STYLE.items())
    header.append(f"  graph [{graph_attrs}];")
    header.append(f"  node [fontname=\"{NODE_FONT}\"];\n")

    body = sorted(nodes)
    body.extend(sorted(edges))
    footer = ["}"]
    return "\n".join(header + body + footer)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    try:
        manifest = load_manifest(args.input)
    except ManifestError as exc:
        print(f"[ERR] {exc}")
        return 1

    nodes, edges = build_graph(manifest, max(0, args.max_topics))

    output = render_graph(nodes, edges)
    args.output.write_text(output, encoding="utf-8")
    print(f"[OK] wrote {args.output}. Render with: dot -Tpng {args.output} -o echo_network.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
