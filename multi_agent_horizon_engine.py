from __future__ import annotations

"""Coordinated horizon simulations across multiple collaborating agents."""

from dataclasses import dataclass
from typing import Dict, Mapping

from horizon_engine import HorizonConfig, HorizonEngine, HorizonResult


@dataclass
class AgentReport:
    name: str
    config: HorizonConfig
    result: HorizonResult


class MultiAgentHorizonEngine:
    """Runs multiple HorizonEngine instances and synthesizes their outputs."""

    def __init__(self, agent_configs: Mapping[str, HorizonConfig]):
        if not agent_configs:
            raise ValueError("At least one agent config is required")
        self.agent_configs = dict(agent_configs)

    def run(self) -> Dict[str, AgentReport]:
        reports: Dict[str, AgentReport] = {}
        for name, config in self.agent_configs.items():
            engine = HorizonEngine(config=config)
            result = engine.run()
            reports[name] = AgentReport(name=name, config=config, result=result)
        return reports

    def synthesize_probability(self, reports: Mapping[str, AgentReport]) -> float:
        """Combine agent probabilities using a simple average."""

        if not reports:
            return 0.0
        return sum(report.result.probability for report in reports.values()) / len(reports)

    def render_bridge(self, reports: Mapping[str, AgentReport]) -> str:
        """Render a compact bridge summary across agent runs."""

        lines = ["🌉 MULTI-AGENT HORIZON BRIDGE", "-----------------------------"]
        for name, report in reports.items():
            lines.append(
                f"{name}: forever-prob={report.result.probability * 100:.3f}% | "
                f"survived={report.result.survived}/{report.config.timelines}"
            )
        lines.append("-----------------------------")
        lines.append(f"synthesized probability: {self.synthesize_probability(reports) * 100:.3f}%")
        return "\n".join(lines)
