"""Filesystem-oriented audit modules."""
from __future__ import annotations

from dataclasses import dataclass, field
import os
import stat
from typing import Iterable, Sequence

from ..config import AuditTarget
from ..types import Finding
from .base import AuditModule


@dataclass
class SecretPatternAudit(AuditModule):
    """Search for potentially sensitive artefacts committed to the repo."""

    name: str = "secret_pattern"
    suspicious_names: Sequence[str] = ("secret", "token", "private", "credential", "key")
    max_bytes: int = 256

    def supports(self, target: AuditTarget) -> bool:  # pragma: no cover - trivial
        return target.kind == "filesystem"

    def collect(self, target: AuditTarget) -> Iterable[Finding]:
        for root, _, files in os.walk(target.path):
            for filename in files:
                lowercase = filename.lower()
                if any(pattern in lowercase for pattern in self.suspicious_names):
                    full_path = os.path.join(root, filename)
                    size = os.path.getsize(full_path)
                    if size <= self.max_bytes:
                        continue
                    yield Finding(
                        module=self.name,
                        target=target.name,
                        description=f"Suspicious artefact '{filename}' detected",
                        severity="high" if size > 4096 else "medium",
                        metadata={"path": full_path, "size": str(size)},
                    )


@dataclass
class WorldWritableAudit(AuditModule):
    """Identify world-writable files that could be modified by untrusted users."""

    name: str = "world_writable"

    def supports(self, target: AuditTarget) -> bool:  # pragma: no cover - trivial
        return target.kind == "filesystem"

    def collect(self, target: AuditTarget) -> Iterable[Finding]:
        for root, _, files in os.walk(target.path):
            for filename in files:
                path = os.path.join(root, filename)
                try:
                    mode = os.stat(path).st_mode
                except FileNotFoundError:
                    continue
                if mode & stat.S_IWOTH:
                    yield Finding(
                        module=self.name,
                        target=target.name,
                        description=f"World-writable file detected: {filename}",
                        severity="critical",
                        metadata={"path": path, "mode": oct(stat.S_IMODE(mode))},
                    )
