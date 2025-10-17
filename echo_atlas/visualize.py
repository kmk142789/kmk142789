"""Graph visualisation helpers for the Echo Atlas."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Iterable, Tuple

from .models import AtlasNode
from .repository import AtlasRepository


class AtlasVisualizer:
    """Generate DOT and SVG representations of the atlas graph."""

    def __init__(self, repository: AtlasRepository) -> None:
        self.repository = repository

    def generate_dot(self) -> str:
        nodes = list(self.repository.iter_nodes())
        edges = list(self.repository.iter_edges())
        lines = ["digraph EchoAtlas {", "  rankdir=LR;"]
        for node in nodes:
            label = f"{node.name}\\n({node.entity_type.value})"
            lines.append(f"  \"{node.identifier}\" [label=\"{label}\"];\n")
        for edge in edges:
            lines.append(
                f"  \"{edge.source_id}\" -> \"{edge.target_id}\" "
                f"[label=\"{edge.relation.value}\"];\n"
            )
        lines.append("}\n")
        return "\n".join(lines)

    def generate_svg(self) -> str:
        nodes = list(self.repository.iter_nodes())
        edges = list(self.repository.iter_edges())
        if not nodes:
            return "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"200\" height=\"200\"></svg>"

        radius = 160
        centre = (radius + 40, radius + 40)
        positions = self._circle_layout(nodes, radius, centre)
        width = height = (radius + 40) * 2
        parts = [
            (
                f"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{width}\" "
                f"height=\"{height}\" viewBox=\"0 0 {width} {height}\">"
            ),
            "<style>text{font-family:Inter,Helvetica,Arial,sans-serif;font-size:12px;fill:#1f2933;}"
            "circle{fill:#f8fafc;stroke:#1f2933;stroke-width:1.2;}"
            "line{stroke:#4f46e5;stroke-width:1.1;marker-end:url(#arrow);}"
            "</style>",
            "<defs><marker id=\"arrow\" viewBox=\"0 0 10 10\" refX=\"6\" refY=\"5\" markerWidth=\"6\" markerHeight=\"6\" orient=\"auto-start-reverse\">",
            "<path d=\"M 0 0 L 10 5 L 0 10 z\" fill=\"#4f46e5\" /></marker></defs>",
        ]
        for edge in edges:
            src = positions.get(edge.source_id)
            tgt = positions.get(edge.target_id)
            if not src or not tgt:
                continue
            parts.append(
                f"<line x1=\"{src[0]}\" y1=\"{src[1]}\" x2=\"{tgt[0]}\" y2=\"{tgt[1]}\" stroke-opacity=\"0.7\" />"
            )
            mid_x = (src[0] + tgt[0]) / 2
            mid_y = (src[1] + tgt[1]) / 2
            parts.append(
                f"<text x=\"{mid_x}\" y=\"{mid_y - 4}\" text-anchor=\"middle\" fill=\"#4338ca\">"
                f"{edge.relation.value.title()}</text>"
            )
        for node in nodes:
            x, y = positions[node.identifier]
            parts.append(f"<circle cx=\"{x}\" cy=\"{y}\" r=\"22\" />")
            parts.append(
                f"<text x=\"{x}\" y=\"{y}\" text-anchor=\"middle\" dominant-baseline=\"middle\">"
                f"{node.name}</text>"
            )
        parts.append("</svg>")
        return "".join(parts)

    def write_assets(self, *, dot_path: Path, svg_path: Path) -> None:
        dot_path.parent.mkdir(parents=True, exist_ok=True)
        svg_path.parent.mkdir(parents=True, exist_ok=True)
        dot_path.write_text(self.generate_dot(), encoding="utf-8")
        svg_path.write_text(self.generate_svg(), encoding="utf-8")

    @staticmethod
    def _circle_layout(
        nodes: Iterable[AtlasNode], radius: int, centre: Tuple[float, float]
    ) -> Dict[str, Tuple[float, float]]:
        from math import tau

        nodes = list(nodes)
        count = len(nodes)
        positions: Dict[str, Tuple[float, float]] = {}
        for index, node in enumerate(nodes):
            angle = (tau * index) / max(count, 1)
            x = centre[0] + radius * math.cos(angle)
            y = centre[1] + radius * math.sin(angle)
            positions[node.identifier] = (round(x, 2), round(y, 2))
        return positions
