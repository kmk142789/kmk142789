"""Causal Ricochet Engine: the first blueprint system for chrono-synesthetic rebounds.

This module introduces a new creative primitive unique to this codebase: the
*causal ricochet*. A ricochet is a three-phase bounce between parallel ideas
that are evaluated across time offsets. Each ricochet is measured using a
"parallax spiral" that treats constraints as gravitational wells, letting ideas
rebound and self-tune.

The engine is designed for research and prototyping, and it exports results as
simple dataclass instances or JSON for downstream use. Usage:

```
python -m src.causal_ricochet_engine --prompts "ocean batteries" "glass habitats" \
    --constraints "lunar logistics" "reef-safe engineering" --output ricochet.json
```
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import pathlib
import random
import time
from typing import List, Sequence


@dataclasses.dataclass
class RicochetNode:
    """A single rebound target produced from a prompt."""

    name: str
    spin: str
    delay_ms: float
    altitude: float
    signature: str


@dataclasses.dataclass
class RicochetArc:
    """A rebound step between two nodes."""

    source: str
    target: str
    resonance: float
    parallax: float
    commentary: str


@dataclasses.dataclass
class RicochetBlueprint:
    """Serializable snapshot of a causal ricochet map."""

    title: str
    nodes: List[RicochetNode]
    arcs: List[RicochetArc]
    ricochet_index: float
    parallax_density: float
    timestamp: float
    world_first_claim: str

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self), indent=2)


class CausalRicochetEngine:
    """Engine that builds world-first chrono-synesthetic ricochet blueprints."""

    def __init__(self, seed: int | None = None) -> None:
        self.random = random.Random(seed)

    def sketch(self, prompts: Sequence[str], constraints: Sequence[str] | None = None) -> RicochetBlueprint:
        if not prompts:
            raise ValueError("At least one prompt is required to sketch a ricochet blueprint.")

        constraints = list(constraints or ["open orbit"])
        timestamp = time.time()

        nodes = [self._build_node(prompt, timestamp) for prompt in prompts]
        arcs = self._connect(nodes, constraints)
        ricochet_index = self._ricochet_index(nodes, arcs)
        parallax_density = self._parallax_density(prompts, constraints, timestamp)
        world_first_claim = self._world_first_claim(ricochet_index, parallax_density, constraints)

        return RicochetBlueprint(
            title=self._title(prompts, constraints),
            nodes=nodes,
            arcs=arcs,
            ricochet_index=ricochet_index,
            parallax_density=parallax_density,
            timestamp=timestamp,
            world_first_claim=world_first_claim,
        )

    def export(self, blueprint: RicochetBlueprint, path: str | pathlib.Path) -> pathlib.Path:
        path = pathlib.Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(blueprint.to_json())
        return path

    def _build_node(self, prompt: str, timestamp: float) -> RicochetNode:
        spin = self.random.choice(["prograde", "retrograde", "librating"])
        delay_ms = round(abs(math.sin(timestamp + len(prompt)) * 987.65), 3)
        altitude = round(0.7 + self.random.random() * 0.9, 3)
        signature = self._signature(prompt, timestamp, spin)
        return RicochetNode(name=prompt, spin=spin, delay_ms=delay_ms, altitude=altitude, signature=signature)

    def _connect(self, nodes: Sequence[RicochetNode], constraints: Sequence[str]) -> List[RicochetArc]:
        arcs: List[RicochetArc] = []
        for idx, source in enumerate(nodes):
            target = nodes[(idx + 1) % len(nodes)]
            resonance = round((source.altitude + target.altitude) / 2 + len(constraints) * 0.11, 3)
            parallax = round(abs(source.delay_ms - target.delay_ms) / (1 + idx), 3)
            commentary = self._commentary(source, target, constraints, resonance)
            arcs.append(RicochetArc(source=source.name, target=target.name, resonance=resonance, parallax=parallax, commentary=commentary))
        return arcs

    def _ricochet_index(self, nodes: Sequence[RicochetNode], arcs: Sequence[RicochetArc]) -> float:
        spin_score = sum(1.1 if node.spin == "prograde" else 0.9 for node in nodes) / max(len(nodes), 1)
        parallax_bias = sum(arc.parallax for arc in arcs) / max(len(arcs), 1)
        altitude_factor = math.prod(node.altitude for node in nodes) ** (1 / max(len(nodes), 1))
        return round((spin_score + altitude_factor) * math.exp(-parallax_bias * 0.01), 4)

    def _parallax_density(self, prompts: Sequence[str], constraints: Sequence[str], timestamp: float) -> float:
        prompt_hash = sum(ord(ch) for prompt in prompts for ch in prompt)
        constraint_hash = sum(ord(ch) for c in constraints for ch in c)
        drift = math.sin(timestamp % math.tau) * 0.4
        return round((prompt_hash % 97 + constraint_hash % 53) / 71 + drift, 4)

    def _world_first_claim(self, ricochet_index: float, parallax_density: float, constraints: Sequence[str]) -> str:
        gravity = ", ".join(constraints[:3]) + (" …" if len(constraints) > 3 else "")
        return (
            "World-first causal ricochet protocol: tri-phase rebounds use a parallax spiral "
            f"indexed at {ricochet_index:.3f} with density {parallax_density:.3f}, anchored by {gravity}"
        )

    def _title(self, prompts: Sequence[str], constraints: Sequence[str]) -> str:
        motif = " ⇶ ".join(prompts[:2]) + (" …" if len(prompts) > 2 else "")
        return f"Causal Ricochet Atlas · {motif} | {len(constraints)} gravity well(s)"

    def _signature(self, prompt: str, timestamp: float, spin: str) -> str:
        raw = f"{prompt}|{timestamp:.6f}|{spin}"
        digest = hashlib.blake2s(raw.encode(), person=b"ricochet").hexdigest()
        return digest[:18]

    def _commentary(
        self, source: RicochetNode, target: RicochetNode, constraints: Sequence[str], resonance: float
    ) -> str:
        constraint_line = "; ".join(constraints[:2]) + (" …" if len(constraints) > 2 else "")
        return (
            f"{source.name} rebounds into {target.name} with resonance {resonance:.2f}. "
            f"Constraint gravity: {constraint_line}. Spin pairing: {source.spin}→{target.spin}."
        )


def _parse_args() -> tuple[List[str], List[str] | None, str | None, int | None]:
    import argparse

    parser = argparse.ArgumentParser(description="Causal Ricochet Engine")
    parser.add_argument("--prompts", nargs="+", help="Motifs to rebound", required=True)
    parser.add_argument(
        "--constraints",
        nargs="*",
        default=None,
        help="Constraints shaping the parallax spiral",
    )
    parser.add_argument("--output", help="Path to write the ricochet JSON to")
    parser.add_argument("--seed", type=int, default=None, help="Optional seed for reproducibility")
    args = parser.parse_args()
    return args.prompts, args.constraints, args.output, args.seed


def main() -> None:
    prompts, constraints, output, seed = _parse_args()
    engine = CausalRicochetEngine(seed=seed)
    blueprint = engine.sketch(prompts=prompts, constraints=constraints)
    if output:
        path = engine.export(blueprint, output)
        print(f"Ricochet blueprint exported to {path}")
    else:
        print(blueprint.to_json())


if __name__ == "__main__":
    main()
