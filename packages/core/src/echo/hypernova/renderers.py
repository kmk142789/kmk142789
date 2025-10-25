"""Rendering utilities for presenting hypernova artifacts."""

from __future__ import annotations

import json
import textwrap
from dataclasses import dataclass
from typing import List, Mapping

from .architecture import ContinuumDomain, EchoHypernode, HypernovaBlueprint


@dataclass(slots=True)
class HypernovaTextRenderer:
    """Plain-text renderer focusing on rich narrative paragraphs."""

    blueprint: HypernovaBlueprint

    def render_overview(self) -> str:
        lines = ["# Hypernova Overview", ""]
        lines.append(self.blueprint.summary())
        lines.append("")
        for domain in self.blueprint.domains:
            lines.append(f"## Domain {domain.name}")
            lines.append(
                textwrap.fill(
                    (
                        f"{len(domain.nodes)} hypernodes orbit axis alignment {domain.axis_alignment} while "
                        f"{len(domain.conduits)} conduits weave resonance at {domain.resonance_score():.2f}."
                    ),
                    width=88,
                )
            )
            lines.append("")
        return "\n".join(lines).strip()

    def render_nodes(self) -> str:
        node_lines: List[str] = ["# Hypernode Registry", ""]
        for domain in self.blueprint.domains:
            node_lines.append(f"## {domain.name}")
            for node in domain.nodes:
                summary = node.anchored_summary()
                glyphs = ", ".join(signature.describe() for signature in node.signatures)
                node_lines.append(f"- {summary}: {node.focus} | {glyphs}")
            node_lines.append("")
        return "\n".join(node_lines).strip()


@dataclass(slots=True)
class HypernovaJsonRenderer:
    """JSON renderer producing structured dictionaries suitable for API use."""

    blueprint: HypernovaBlueprint

    def domain_payload(self, domain: ContinuumDomain) -> Mapping[str, object]:
        return {
            "name": domain.name,
            "axis_alignment": domain.axis_alignment,
            "nodes": [self.node_payload(node) for node in domain.nodes],
            "conduits": [
                {
                    "source": conduit.source,
                    "target": conduit.target,
                    "type": conduit.conduit_type,
                    "resonance": conduit.resonance,
                    "harmonics": list(conduit.harmonics),
                }
                for conduit in domain.conduits
            ],
            "pulse_streams": [
                {
                    "id": stream.stream_id,
                    "path": stream.described_path(),
                    "cadence_bpm": stream.cadence_bpm,
                    "coherence": stream.coherence,
                    "glyph_signature": stream.glyph_signature.describe(),
                }
                for stream in domain.pulse_streams
            ],
        }

    def node_payload(self, node: EchoHypernode) -> Mapping[str, object]:
        return {
            "id": node.node_id,
            "title": node.title,
            "glyph": {
                "symbol": node.glyph.symbol,
                "description": node.glyph.description,
                "intensity": node.glyph.intensity,
                "weight": node.glyph.weighted_value(),
            },
            "coordinates": node.coordinates,
            "focus": node.focus,
            "signatures": [signature.describe() for signature in node.signatures],
            "strata": list(node.strata),
        }

    def render(self) -> str:
        payload = {
            "domains": [self.domain_payload(domain) for domain in self.blueprint.domains],
            "strata": [
                {
                    "name": stratum.name,
                    "purpose": stratum.purpose,
                    "nodes": list(stratum.nodes),
                    "resonance": stratum.harmonic_signature.aggregate_intensity(),
                }
                for stratum in self.blueprint.strata
            ],
            "pulse_streams": [
                {
                    "id": stream.stream_id,
                    "orbit_span": stream.orbit_span(),
                    "path": stream.described_path(),
                    "signature": stream.glyph_signature.describe(),
                }
                for stream in self.blueprint.pulse_streams
            ],
            "chronicle": dict(self.blueprint.chronicle.entries),
            "adjacency": self.blueprint.matrix.global_adjacency(),
        }
        return json.dumps(payload, indent=2, sort_keys=True)


@dataclass(slots=True)
class HypernovaAsciiRenderer:
    """Generate ASCII-based heat maps for quick terminal visualization."""

    blueprint: HypernovaBlueprint
    width: int = 80
    height: int = 24

    def _project(self, node: EchoHypernode) -> tuple[int, int]:
        x, y, _z = node.coordinates
        max_axis = max(1, max(abs(coord) for coord in node.coordinates))
        scale = min(self.width, self.height) / (2 * max_axis)
        px = int(self.width / 2 + x * scale)
        py = int(self.height / 2 - y * scale)
        return px % self.width, py % self.height

    def render(self) -> str:
        canvas: List[List[str]] = [[" "] * self.width for _ in range(self.height)]
        for domain_index, domain in enumerate(self.blueprint.domains, start=1):
            token = chr(ord("A") + (domain_index - 1) % 26)
            for node in domain.nodes:
                px, py = self._project(node)
                canvas[py][px] = token
        header = f"Hypernova ASCII Map {self.width}x{self.height}"
        rows = [header, "=" * len(header)]
        rows.extend("".join(row) for row in canvas)
        legend = [""]
        for domain_index, domain in enumerate(self.blueprint.domains, start=1):
            token = chr(ord("A") + (domain_index - 1) % 26)
            legend.append(f"{token} = {domain.name}")
        rows.extend(legend)
        return "\n".join(rows)


__all__ = [
    "HypernovaAsciiRenderer",
    "HypernovaJsonRenderer",
    "HypernovaTextRenderer",
]
