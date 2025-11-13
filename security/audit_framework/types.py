"""Shared datatypes for the audit framework."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Mapping, Optional


@dataclass
class Finding:
    """Result produced by an audit module."""

    module: str
    target: str
    description: str
    severity: str
    metadata: Mapping[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ThreatSignal:
    """Enriched finding with threat scoring information."""

    finding: Finding
    score: float
    category: str
    recommendation: Optional[str] = None

    def is_actionable(self, threshold: float) -> bool:
        """Return True when the signal exceeds the configured threshold."""

        return self.score >= threshold
