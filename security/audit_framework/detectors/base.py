"""Base classes for threat detectors."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from ..config import FrameworkConfig
from ..types import Finding, ThreatSignal


class ThreatDetector(ABC):
    """Convert findings into scored threat signals."""

    name: str = "detector"

    @abstractmethod
    def analyze(self, finding: Finding, config: FrameworkConfig) -> ThreatSignal:
        raise NotImplementedError

    def bulk(self, findings: Iterable[Finding], config: FrameworkConfig) -> Iterable[ThreatSignal]:
        for finding in findings:
            yield self.analyze(finding, config)
