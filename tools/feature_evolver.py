"""Feature Evolver utility.

This module introduces a small showcase that delivers a sequence of
features.  Each successive feature is intentionally more sophisticated
than the previous one so we can demonstrate the idea of "create and
implement more and more complex features each time" that the user
requested.  The script ships with a tiny CLI so contributors can run
the evolving pipeline locally or export the results to JSON for further
analysis.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import json
import statistics
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
import random


@dataclass
class FeatureInsight:
    """Container describing a generated feature."""

    level: int
    name: str
    description: str
    payload: Dict[str, object]


class FeatureEvolver:
    """Generate increasingly complex features."""

    def __init__(self, seed: int = 1337) -> None:
        self.random = random.Random(seed)
        self.idea_pool = [
            {"name": "Telemetry Overlay", "complexity": 2, "confidence": 0.78},
            {"name": "Insight Timeline", "complexity": 3, "confidence": 0.72},
            {"name": "Autonomous Narrative", "complexity": 4, "confidence": 0.81},
            {"name": "Dynamic Risk Lens", "complexity": 5, "confidence": 0.69},
            {"name": "Systems Chorus", "complexity": 4, "confidence": 0.74},
        ]
        self.dependencies = {
            "Telemetry Overlay": [],
            "Insight Timeline": ["Telemetry Overlay"],
            "Autonomous Narrative": ["Telemetry Overlay"],
            "Dynamic Risk Lens": ["Insight Timeline", "Autonomous Narrative"],
            "Systems Chorus": ["Dynamic Risk Lens"],
        }
        self.base_durations = {
            "Telemetry Overlay": 1.5,
            "Insight Timeline": 2.0,
            "Autonomous Narrative": 2.5,
            "Dynamic Risk Lens": 3.5,
            "Systems Chorus": 1.0,
        }

    def level_one_storyboard(self) -> FeatureInsight:
        """Return a creative feature description (lowest complexity)."""

        pick_count = 3
        ideas = self.idea_pool[:pick_count]
        confidence = statistics.mean(i["confidence"] for i in ideas)
        description = (
            "Sketches a foundational concept deck that highlights value statements "
            "and immediately actionable hooks."
        )
        payload = {
            "complexity_tier": 1,
            "tagline": "A spark of intent",
            "ideas": [i["name"] for i in ideas],
            "confidence": round(confidence, 2),
        }
        return FeatureInsight(1, "Concept Storyboard", description, payload)

    def level_two_requirement_matrix(self) -> FeatureInsight:
        """Aggregate small-scale planning metrics."""

        complexities = [i["complexity"] for i in self.idea_pool]
        avg_complexity = statistics.mean(complexities)
        stdev = statistics.pstdev(complexities)
        focus = [i for i in self.idea_pool if i["complexity"] >= avg_complexity]
        description = (
            "Converts storyboard ideas into a requirement matrix with summary "
            "statistics to guide prioritisation."
        )
        payload = {
            "complexity_tier": 2,
            "avg_complexity": round(avg_complexity, 2),
            "complexity_stdev": round(stdev, 2),
            "high_leverage": [i["name"] for i in focus],
        }
        return FeatureInsight(2, "Requirement Matrix", description, payload)

    def level_three_dependency_projection(self) -> FeatureInsight:
        """Compute the dependency order and earliest possible schedule."""

        order = self._topological_order()
        start_times = self._earliest_start(order)
        description = (
            "Elevates the matrix into a dependency projection with deterministic "
            "ordering and earliest start times."
        )
        payload = {
            "complexity_tier": 3,
            "order": order,
            "starts": {k: round(v, 2) for k, v in start_times.items()},
        }
        return FeatureInsight(3, "Dependency Projection", description, payload)

    def level_four_risk_simulation(self, trials: int = 250) -> FeatureInsight:
        """Simulate execution risk using a small Monte Carlo approach."""

        completion_times = [self._simulate_duration() for _ in range(trials)]
        threshold = 12.0
        probability = sum(t <= threshold for t in completion_times) / trials
        description = (
            "Runs a Monte Carlo schedule simulation using dependency-aware "
            "durations, providing a probability of delivering within the "
            "target window."
        )
        payload = {
            "complexity_tier": 4,
            "threshold": threshold,
            "probability": round(probability, 2),
            "p95_completion": round(self._percentile(completion_times, 0.95), 2),
        }
        return FeatureInsight(4, "Risk Simulation", description, payload)

    def run_levels(self, max_level: int = 4) -> List[FeatureInsight]:
        """Run all levels up to *max_level* and return their insights."""

        level_map = {
            1: self.level_one_storyboard,
            2: self.level_two_requirement_matrix,
            3: self.level_three_dependency_projection,
            4: self.level_four_risk_simulation,
        }
        insights: List[FeatureInsight] = []
        for level in range(1, max_level + 1):
            if level not in level_map:
                raise ValueError(f"Unsupported level: {level}")
            insights.append(level_map[level]())
        return insights

    def _topological_order(self) -> List[str]:
        indegree: Dict[str, int] = {node: 0 for node in self.dependencies}
        for deps in self.dependencies.values():
            for dep in deps:
                indegree[dep] += 0  # ensure key exists
        for node, deps in self.dependencies.items():
            for dep in deps:
                indegree[node] += 1
        queue = [node for node, degree in indegree.items() if degree == 0]
        order: List[str] = []
        while queue:
            node = queue.pop(0)
            order.append(node)
            for successor, deps in self.dependencies.items():
                if node in deps:
                    indegree[successor] -= 1
                    if indegree[successor] == 0:
                        queue.append(successor)
        if len(order) != len(self.dependencies):
            raise RuntimeError("Cycle detected in dependency graph")
        return order

    def _earliest_start(self, order: Iterable[str]) -> Dict[str, float]:
        start_times: Dict[str, float] = {}
        for node in order:
            deps = self.dependencies.get(node, [])
            earliest = max((start_times[d] + self.base_durations[d] for d in deps), default=0.0)
            start_times[node] = earliest
        return start_times

    def _simulate_duration(self) -> float:
        order = self._topological_order()
        starts = self._earliest_start(order)
        completion = 0.0
        for node in order:
            base = self.base_durations[node]
            jitter = self.random.uniform(-0.3, 0.5)
            completion = max(completion, starts[node] + base + jitter)
        return completion

    def _percentile(self, data: Iterable[float], ratio: float) -> float:
        ordered = sorted(data)
        index = min(len(ordered) - 1, int(round((len(ordered) - 1) * ratio)))
        return ordered[index]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate sequential feature insights.")
    parser.add_argument("--max-level", type=int, default=4, help="Highest feature level to compute")
    parser.add_argument("--seed", type=int, default=1337, help="Seed for deterministic runs")
    parser.add_argument(
        "--export",
        type=Path,
        default=None,
        help="Optional JSON file to write the generated insights",
    )
    args = parser.parse_args()

    evolver = FeatureEvolver(seed=args.seed)
    insights = evolver.run_levels(args.max_level)

    for insight in insights:
        print(f"Level {insight.level}: {insight.name}")
        print(f"  {insight.description}")
        for key, value in insight.payload.items():
            print(f"    - {key}: {value}")
        print()

    if args.export:
        args.export.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(insight) for insight in insights]
        args.export.write_text(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
