"""Detectors that score findings."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Optional

from ..config import FrameworkConfig
from ..types import Finding, ThreatSignal
from .base import ThreatDetector


@dataclass
class SeverityScoringDetector(ThreatDetector):
    """Score findings based on severity and contextual metadata."""

    name: str = "severity_scoring"
    category_overrides: Optional[Mapping[str, str]] = None

    def analyze(self, finding: Finding, config: FrameworkConfig) -> ThreatSignal:
        weights = config.severity_weights
        base_score = weights.get(finding.severity.lower(), 0.1)
        metadata_bonus = 0.0
        if "path" in finding.metadata and "secrets" in finding.metadata.get("path", ""):
            metadata_bonus += 0.1
        if finding.metadata.get("mode") == "0o777":
            metadata_bonus += 0.2
        score = min(1.0, base_score + metadata_bonus)
        category = "data_exposure" if "secret" in finding.description.lower() else "configuration"
        if self.category_overrides and finding.module in self.category_overrides:
            category = self.category_overrides[finding.module]
        recommendation = None
        if category == "data_exposure":
            recommendation = "Rotate credentials and purge sensitive artefacts."
        elif category == "configuration":
            recommendation = "Tighten file permissions and enforce infrastructure as code."
        return ThreatSignal(
            finding=finding,
            score=score,
            category=category,
            recommendation=recommendation,
        )


def default_detectors() -> Dict[str, ThreatDetector]:
    return {"severity_scoring": SeverityScoringDetector()}
