"""Core orchestrator for the modular security audit framework."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence

from .config import AuditTarget, FrameworkConfig
from .detectors.scoring import SeverityScoringDetector, default_detectors
from .modules.base import AuditModule
from .modules.dependencies import NodeDependencyAudit, PythonDependencyAudit
from .modules.filesystem import SecretPatternAudit, WorldWritableAudit
from .types import Finding, ThreatSignal


@dataclass
class SecurityAuditFramework:
    """Coordinate audit modules and threat detectors."""

    modules: Sequence[AuditModule] = field(
        default_factory=lambda: (
            SecretPatternAudit(),
            WorldWritableAudit(),
            PythonDependencyAudit(),
            NodeDependencyAudit(),
        )
    )
    detector_registry: Dict[str, SeverityScoringDetector] = field(
        default_factory=lambda: dict(default_detectors())
    )

    def list_modules(self) -> List[str]:  # pragma: no cover - trivial helper
        return [module.name for module in self.modules]

    def register_detector(self, name: str, detector: SeverityScoringDetector) -> None:
        self.detector_registry[name] = detector

    def run(
        self,
        targets: Iterable[AuditTarget],
        config: FrameworkConfig | None = None,
    ) -> Dict[str, List[ThreatSignal]]:
        config = config or FrameworkConfig()
        findings = self._collect_findings(targets)
        signals = self._detect(findings, config)
        return signals

    def _collect_findings(self, targets: Iterable[AuditTarget]) -> List[Finding]:
        findings: List[Finding] = []
        for target in targets:
            for module in self.modules:
                if not module.supports(target):
                    continue
                for finding in module.collect(target):
                    findings.append(finding)
        return findings

    def _detect(
        self, findings: Iterable[Finding], config: FrameworkConfig
    ) -> Dict[str, List[ThreatSignal]]:
        detectors = config.detectors or self.detector_registry.keys()
        signals: Dict[str, List[ThreatSignal]] = defaultdict(list)
        for finding in findings:
            for detector_name in detectors:
                detector = self.detector_registry.get(detector_name)
                if detector is None:
                    continue
                signal = detector.analyze(finding, config)
                signals[finding.target].append(signal)
        return signals
