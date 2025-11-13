"""Configuration models for the security audit framework."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


@dataclass
class AuditTarget:
    """Describes a surface that should be analysed by audit modules."""

    name: str
    path: str
    kind: str = "filesystem"
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class FrameworkConfig:
    """Top-level configuration for orchestrating audits and detections."""

    severity_weights: Dict[str, float] = field(
        default_factory=lambda: {"low": 0.1, "medium": 0.4, "high": 0.7, "critical": 1.0}
    )
    detectors: Optional[Iterable[str]] = None
    fail_on_score: float = 0.75
    max_findings: Optional[int] = None
    notes: List[str] = field(default_factory=list)
