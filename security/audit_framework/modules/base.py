"""Base classes for audit modules."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from ..config import AuditTarget
from ..types import Finding


class AuditModule(ABC):
    """Abstract building block for running security audits."""

    name: str = "base"

    def supports(self, target: AuditTarget) -> bool:
        """Return True if the module can analyse the provided target."""

        return True

    @abstractmethod
    def collect(self, target: AuditTarget) -> Iterable[Finding]:
        """Run the module against a target and yield findings."""

        raise NotImplementedError
