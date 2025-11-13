"""Modular framework for automated security auditing and threat detection."""

from .config import AuditTarget, FrameworkConfig
from .types import Finding, ThreatSignal
from .framework import SecurityAuditFramework

__all__ = [
    "AuditTarget",
    "FrameworkConfig",
    "Finding",
    "ThreatSignal",
    "SecurityAuditFramework",
]
