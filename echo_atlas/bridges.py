"""Bridge DreamCompiler, Ledger, and Keysmith outputs into Atlas graphs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple


@dataclass(frozen=True)
class BridgeNode:
    identifier: str
    label: str
    kind: str


@dataclass(frozen=True)
class BridgeEdge:
    source: str
    target: str
    relation: str


class AtlasBridge:
    """Simple directed graph that records weave activity."""

    def __init__(self, *, docs_root: Path | None = None) -> None:
        self.nodes: Dict[str, BridgeNode] = {}
        self.edges: Set[BridgeEdge] = set()
        self.docs_root = docs_root or Path("docs") / "poetry"
        self.docs_root.mkdir(parents=True, exist_ok=True)

    def add_receipt(self, receipt: dict) -> str:
        identifier = f"receipt:{receipt['sha256_of_diff']}"
        self.nodes[identifier] = BridgeNode(identifier=identifier, label=receipt["rhyme"], kind="receipt")
        return identifier

    def add_attestation(self, attestation: dict) -> str:
        identifier = f"attest:{attestation.get('key', 'none')}"
        label = "valid" if attestation.get("valid") else "invalid"
        self.nodes[identifier] = BridgeNode(identifier=identifier, label=label, kind="attestation")
        return identifier

    def connect(self, source: str, target: str, relation: str) -> None:
        self.edges.add(BridgeEdge(source=source, target=target, relation=relation))

    def summary(self) -> dict:
        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
        }

    def to_dot(self) -> str:
        lines = ["digraph loom {"]
        for node in sorted(self.nodes.values(), key=lambda n: n.identifier):
            lines.append(f'  "{node.identifier}" [label="{node.label} ({node.kind})"];')
        for edge in sorted(self.edges, key=lambda e: (e.source, e.target)):
            lines.append(f'  "{edge.source}" -> "{edge.target}" [label="{edge.relation}"];')
        lines.append("}")
        return "\n".join(lines)

    def to_svg(self) -> str:
        width = 320
        height = 80 + 40 * max(len(self.nodes), 1)
        lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
            '<style>text{font-family:monospace;font-size:12px;}</style>',
        ]
        for idx, node in enumerate(sorted(self.nodes.values(), key=lambda n: n.identifier)):
            y = 40 + idx * 40
            lines.append(f'<circle cx="40" cy="{y}" r="12" fill="#4F46E5" data-node="{node.identifier}" />')
            lines.append(f'<text x="70" y="{y + 4}" data-node="{node.identifier}">{node.label}</text>')
        sorted_keys = list(sorted(self.nodes))
        for edge in sorted(self.edges, key=lambda e: (e.source, e.target)):
            y1 = 40 + sorted_keys.index(edge.source) * 40
            y2 = 40 + sorted_keys.index(edge.target) * 40
            lines.append(
                f'<line x1="40" y1="{y1}" x2="220" y2="{y2}" '
                f'stroke="#0EA5E9" stroke-width="2" data-edge="{edge.source}->{edge.target}" />'
            )
        lines.append("</svg>")
        return "\n".join(lines)

    def svg_nodes(self, svg: str) -> Set[str]:
        identifiers: Set[str] = set()
        for part in svg.split("data-node="):
            if part.startswith('"'):
                identifier = part.split('"')[1]
                identifiers.add(identifier)
        return identifiers

    def export(self, *, poem: str, plan: List[dict], receipt: dict, attestation: dict, slug: str) -> Tuple[Path, Path]:
        dot = self.to_dot()
        svg = self.to_svg()
        doc_path = self.docs_root / f"{slug}.md"
        svg_path = self.docs_root / f"{slug}.svg"
        doc_content = [
            f"# Loom Snapshot — {slug}",
            "",
            "## Poem",
            "",
            poem,
            "",
            "## Plan",
            "",
        ]
        for step in plan:
            doc_content.append(f"- {step['index']}. {step['title']}")
        doc_content.extend(
            [
                "",
                "## Pulse Receipt",
                "",
                f"- Rhyme: {receipt['rhyme']}",
                f"- Hash: {receipt['sha256_of_diff']}",
                f"- Result: {receipt['result']}",
                "",
                "## Key Attestation",
                "",
                f"- Valid: {attestation.get('valid', False)}",
                f"- Repaired: {attestation.get('repaired', False)}",
                "",
                "## Graph",
                "",
                "```dot",
                dot,
                "```",
                "",
                f"![{slug} graph]({svg_path.name})",
            ]
        )
        doc_path.write_text("\n".join(doc_content), encoding="utf-8")
        svg_path.write_text(svg, encoding="utf-8")
        return doc_path, svg_path


__all__ = ["AtlasBridge", "BridgeNode", "BridgeEdge"]
