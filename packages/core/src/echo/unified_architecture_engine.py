"""Unified Architecture Engine for Echo.

This module scans the Echo core package, groups historical modules into
layered constellations, and emits a reproducible blueprint that highlights how
creative, operational, and sovereign surfaces interconnect.  It is intentionally
self-contained so it can act as both a CLI helper and a reusable library for
pipelines that need an aggregated architecture view.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import json
from collections import Counter, defaultdict
from typing import Sequence


CATEGORY_RULES = {
    "continuum": ("continuum", "temporal", "timeline", "observatory"),
    "pulse": ("pulse", "heartbeat", "resonance", "telemetry"),
    "bridge": ("bridge", "registry", "manifest", "sync"),
    "creative": ("creative", "story", "aurora", "stellar", "poem"),
    "systems": ("engine", "core", "loop", "orchestrator", "synth"),
    "sovereign": ("sovereign", "guardian", "policy", "charter", "governance"),
    "identity": ("identity", "passport", "credential", "wallet", "did"),
    "attestation": ("attest", "attestation", "verify", "proof", "verifier", "zk"),
    "routing": ("router", "mesh", "gateway", "relay", "nexus", "hub", "fabric"),
}

LAYER_PRIORITIES = {
    "foundation": {"systems", "bridge", "sovereign"},
    "synthesis": {"continuum", "pulse"},
    "expression": {"creative"},
}

KEYSTONE_HINTS = ("core", "engine", "orchestrator", "continuum", "pulse", "bridge")
AUTHORITY_KEYWORDS = {"governance", "guardian", "sovereign", "authority", "policy", "charter", "registry"}


@dataclass(frozen=True)
class ModuleSpec:
    """Representation of a discovered module."""

    name: str
    relative_path: str
    categories: tuple[str, ...]
    tokens: tuple[str, ...]

    @property
    def primary_category(self) -> str:
        return self.categories[0] if self.categories else "frontier"

    @property
    def layer(self) -> str:
        for layer, categories in LAYER_PRIORITIES.items():
            if categories & set(self.categories):
                return layer
        return "frontier"

    @property
    def keystone_score(self) -> int:
        keyword_hits = sum(token in KEYSTONE_HINTS for token in self.tokens)
        return keyword_hits + len(set(self.categories))


class UnifiedArchitectureEngine:
    """Synthesise a unified architecture blueprint for the Echo modules."""

    def __init__(self, module_root: str | Path | None = None) -> None:
        if module_root is None:
            module_root = Path(__file__).resolve().parent
        self.module_root = Path(module_root)
        if not self.module_root.exists():
            raise FileNotFoundError(f"Module root {self.module_root} does not exist")

    # ------------------------------------------------------------------
    # Discovery helpers
    # ------------------------------------------------------------------
    def discover_modules(self) -> list[ModuleSpec]:
        specs: list[ModuleSpec] = []
        for path in sorted(self.module_root.rglob("*.py")):
            if path.name == "__init__.py":
                continue
            relative = path.relative_to(self.module_root).as_posix()
            tokens = self._tokenize(relative)
            categories = self._categorise(tokens)
            specs.append(ModuleSpec(
                name=path.stem,
                relative_path=relative,
                categories=tuple(categories),
                tokens=tuple(tokens),
            ))
        return specs

    # ------------------------------------------------------------------
    # Blueprint construction
    # ------------------------------------------------------------------
    def build_blueprint(self) -> dict:
        modules = self.discover_modules()
        category_map: dict[str, list[ModuleSpec]] = defaultdict(list)
        layer_map: dict[str, list[ModuleSpec]] = defaultdict(list)
        adjacency_counter: Counter[tuple[str, str]] = Counter()
        keystones: list[ModuleSpec] = []
        authority_candidates: list[ModuleSpec] = []
        flow_edges: Counter[tuple[str, str]] = Counter()

        for spec in modules:
            category_map[spec.primary_category].append(spec)
            layer_map[spec.layer].append(spec)
            if len(spec.categories) > 1:
                for i, first in enumerate(spec.categories):
                    for second in spec.categories[i + 1:]:
                        edge = tuple(sorted((first, second)))
                        adjacency_counter[edge] += 1
                        if {"identity", "attestation"} & {first, second}:
                            flow_edges[edge] += 1
            keystones.append(spec)
            if AUTHORITY_KEYWORDS.intersection(spec.tokens) or {
                "sovereign",
                "identity",
                "attestation",
            }.intersection(spec.categories):
                authority_candidates.append(spec)

        keystone_selection = sorted(keystones, key=lambda spec: spec.keystone_score, reverse=True)[:12]
        authority_selection = sorted(
            authority_candidates,
            key=lambda spec: (spec.keystone_score, len(spec.tokens)),
            reverse=True,
        )[:12]

        sovereign_mesh_density = (
            len([edge for edge in adjacency_counter if set(edge) & {"sovereign", "identity", "attestation"}])
            / max(len(adjacency_counter), 1)
        )

        blueprint = {
            "total_modules": len(modules),
            "category_summary": {
                name: {
                    "count": len(items),
                    "sample": [spec.relative_path for spec in items[:8]],
                }
                for name, items in sorted(
                    category_map.items(),
                    key=lambda pair: pair[1].__len__(),
                    reverse=True,
                )
            },
            "layer_summary": {
                layer: {
                    "count": len(items),
                    "categories": sorted({spec.primary_category for spec in items}),
                }
                for layer, items in sorted(
                    layer_map.items(),
                    key=lambda pair: pair[1].__len__(),
                    reverse=True,
                )
            },
            "keystones": [
                {
                    "name": spec.name,
                    "relative_path": spec.relative_path,
                    "categories": spec.categories,
                    "score": spec.keystone_score,
                }
                for spec in keystone_selection
            ],
            "authority_anchors": [
                {
                    "name": spec.name,
                    "relative_path": spec.relative_path,
                    "categories": spec.categories,
                    "score": spec.keystone_score,
                }
                for spec in authority_selection
            ],
            "adjacency": {
                f"{first}<->{second}": count
                for (first, second), count in sorted(
                    adjacency_counter.items(),
                    key=lambda pair: pair[1],
                    reverse=True,
                )
            },
            "identity_flows": {
                f"{first}<->{second}": count
                for (first, second), count in sorted(
                    flow_edges.items(),
                    key=lambda pair: pair[1],
                    reverse=True,
                )
            },
            "sovereign_mesh_density": round(sovereign_mesh_density, 3),
        }
        return blueprint

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def to_markdown(self, blueprint: dict) -> str:
        lines: list[str] = []
        total = blueprint["total_modules"]
        lines.append("# Unified Architecture Blueprint")
        lines.append("")
        lines.append(
            f"Discovered **{total}** Echo modules and reorganised them into layered constellations "
            "that expose foundation systems, synthesis engines, and expressive story surfaces."
        )
        lines.append("")

        lines.append("## Layered Overview")
        for layer, data in blueprint["layer_summary"].items():
            categories = ", ".join(data["categories"]) or "frontier"
            lines.append(f"- **{layer.title()}** · {data['count']} modules · {categories}")
        lines.append("")

        lines.append("## Category Atlas")
        for name, data in blueprint["category_summary"].items():
            sample = ", ".join(data["sample"]) or "(no examples)"
            lines.append(f"- **{name}** ({data['count']} modules) → {sample}")
        lines.append("")

        lines.append("## Keystone Modules")
        for keystone in blueprint["keystones"]:
            cats = ", ".join(keystone["categories"]) or "frontier"
            lines.append(
                f"- `{keystone['relative_path']}` · categories: {cats} · score {keystone['score']}"
            )
        lines.append("")

        authority_anchors = blueprint.get("authority_anchors", [])
        if authority_anchors:
            lines.append("## Authority & Identity Anchors")
            lines.append(
                "Modules binding governance, attestation, and identity across the fabric with "
                "elevated keystone scores."
            )
            for anchor in authority_anchors:
                cats = ", ".join(anchor["categories"]) or "frontier"
                lines.append(
                    f"- `{anchor['relative_path']}` · categories: {cats} · score {anchor['score']}"
                )
            lines.append("")

        adjacency = blueprint["adjacency"]
        if adjacency:
            lines.append("## Convergent Pathways")
            for edge, weight in adjacency.items():
                lines.append(f"- {edge} × {weight}")
            lines.append("")

        identity_flows = blueprint.get("identity_flows")
        mesh_density = blueprint.get("sovereign_mesh_density")
        if identity_flows:
            lines.append("## Identity & Attestation Flows")
            lines.append(
                "Cross-domain pathways where identity or attestation surfaces co-appear with other "
                "categories, highlighting governance-aware routing."
            )
            for edge, weight in identity_flows.items():
                lines.append(f"- {edge} × {weight}")
            lines.append(f"- Sovereign mesh density: {mesh_density}")
            lines.append("")

        lines.append(
            "Use `python -m echo.unified_architecture_engine --json` to stream the raw blueprint into "
            "other research pipelines or `--output docs/UNIFIED_ARCHITECTURE.md` to refresh this file."
        )
        lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------
    def _tokenize(self, relative_path: str) -> tuple[str, ...]:
        path = relative_path.lower().replace(".py", "")
        tokens: list[str] = []
        for segment in path.replace("/", "_").split("_"):
            if segment:
                tokens.append(segment)
        return tuple(tokens)

    def _categorise(self, tokens: Sequence[str]) -> tuple[str, ...]:
        hits: list[str] = []
        for category, keywords in CATEGORY_RULES.items():
            if any(keyword in tokens for keyword in keywords):
                hits.append(category)
        return tuple(dict.fromkeys(hits))


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Echo Unified Architecture Engine")
    parser.add_argument(
        "--module-root",
        type=Path,
        default=None,
        help="Override the module root (defaults to packages/core/src/echo)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write the markdown blueprint",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the raw JSON blueprint to stdout",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)
    engine = UnifiedArchitectureEngine(args.module_root)
    blueprint = engine.build_blueprint()
    markdown = engine.to_markdown(blueprint)

    if args.json:
        print(json.dumps(blueprint, indent=2))
    else:
        print(markdown)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")


if __name__ == "__main__":
    main()
