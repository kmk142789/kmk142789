from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Protocol

from ..policy import PolicyEngine
from ..utils import Finding, isoformat, write_json


class Probe(Protocol):
    name: str

    def run(self, inventory: dict[str, Any]) -> list[Finding]:
        ...


@dataclass
class ProbeReport:
    name: str
    started_at: str
    ended_at: str
    findings: list[Finding] = field(default_factory=list)
    policy_decisions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "findings": [finding.__dict__ for finding in self.findings],
            "policy_decisions": self.policy_decisions,
            "summary": self.summary,
        }

    @property
    def summary(self) -> dict[str, int]:
        counters = {"ok": 0, "info": 0, "warning": 0, "error": 0}
        for finding in self.findings:
            counters[finding.status] = counters.get(finding.status, 0) + 1
        return counters


class ProbeRunner:
    def __init__(self, probes: Iterable[Probe], policy_engine: PolicyEngine | None = None) -> None:
        self.probes = list(probes)
        self.policy_engine = policy_engine or PolicyEngine()

    def run(self, inventory: dict[str, Any]) -> list[ProbeReport]:
        reports: list[ProbeReport] = []
        for probe in self.probes:
            started = isoformat()
            findings = probe.run(inventory)
            decisions = self.policy_engine.evaluate(findings)
            report = ProbeReport(
                name=probe.name,
                started_at=started,
                ended_at=isoformat(),
                findings=findings,
                policy_decisions=[decision.__dict__ for decision in decisions],
            )
            reports.append(report)
        return reports

    def write(self, reports: Iterable[ProbeReport], directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        for report in reports:
            path = directory / f"report-{report.name}.json"
            write_json(path, report.to_dict())


__all__ = ["Probe", "ProbeReport", "ProbeRunner"]

