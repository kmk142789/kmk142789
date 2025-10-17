"""Graph visualization helpers."""

from __future__ import annotations

from math import cos, pi, sin
from pathlib import Path
from typing import Iterable, List

from .domain import Edge, Node
from .utils import ensure_directory


DOT_HEADER = "digraph EchoAtlas {\n  rankdir=LR;\n  node [shape=ellipse, style=filled, fillcolor=lightgoldenrod1];\n}\n"


def build_dot(nodes: Iterable[Node], edges: Iterable[Edge]) -> str:
    lines = ["digraph EchoAtlas {", "  rankdir=LR;"]
    for node in sorted(nodes, key=lambda n: (n.entity_type.value, n.name)):
        lines.append(
            f"  \"{node.identifier}\" [label=\"{node.name}\\n{node.entity_type.value}\"];"
        )
    for edge in sorted(edges, key=lambda e: e.identifier):
        lines.append(
            f"  \"{edge.source}\" -> \"{edge.target}\" [label=\"{edge.relation.value}\"];"
        )
    lines.append("}")
    return "\n".join(lines) + "\n"


def build_svg(nodes: List[Node], edges: List[Edge]) -> str:
    if not nodes:
        return "<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'></svg>"
    radius = 150
    center_x, center_y = 200, 200
    total = len(nodes)
    positions = {}
    for index, node in enumerate(sorted(nodes, key=lambda n: (n.entity_type.value, n.name))):
        angle = 2 * pi * index / max(total, 1)
        x = center_x + radius * cos(angle)
        y = center_y + radius * sin(angle)
        positions[node.identifier] = (x, y, node)
    svg_lines = [
        "<svg xmlns='http://www.w3.org/2000/svg' width='400' height='400'>",
        "  <style>text { font-family: sans-serif; font-size: 12px; }</style>",
    ]
    for edge in sorted(edges, key=lambda e: e.identifier):
        if edge.source not in positions or edge.target not in positions:
            continue
        x1, y1, _ = positions[edge.source]
        x2, y2, _ = positions[edge.target]
        svg_lines.append(
            f"  <line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' stroke='#888' stroke-width='1.5' marker-end='url(#arrow)' />"
        )
    svg_lines.append(
        "  <defs><marker id='arrow' markerWidth='10' markerHeight='10' refX='6' refY='3' orient='auto' markerUnits='strokeWidth'>"
        "<path d='M0,0 L0,6 L9,3 z' fill='#888' /></marker></defs>"
    )
    for node_id, (x, y, node) in positions.items():
        svg_lines.append(
            f"  <circle cx='{x:.1f}' cy='{y:.1f}' r='20' fill='#f5deb3' stroke='#b8860b' stroke-width='1.5' />"
        )
        svg_lines.append(
            f"  <text x='{x:.1f}' y='{y - 25:.1f}' text-anchor='middle'>{node.name}</text>"
        )
        svg_lines.append(
            f"  <text x='{x:.1f}' y='{y + 35:.1f}' text-anchor='middle' fill='#555'>{node.entity_type.value}</text>"
        )
    svg_lines.append("</svg>")
    return "\n".join(svg_lines) + "\n"


def write_dot(path: Path, content: str) -> None:
    ensure_directory(path.parent)
    path.write_text(content, encoding="utf-8")


def write_svg(path: Path, content: str) -> None:
    ensure_directory(path.parent)
    path.write_text(content, encoding="utf-8")
