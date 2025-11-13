"""Audit modules that inspect dependency manifests."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable

from ..config import AuditTarget
from ..types import Finding
from .base import AuditModule


@dataclass
class PythonDependencyAudit(AuditModule):
    """Ensure Python dependencies are pinned and monitored."""

    name: str = "python_dependency"
    manifest_name: str = "requirements.txt"

    def collect(self, target: AuditTarget) -> Iterable[Finding]:
        manifest = Path(target.path) / self.manifest_name
        if not manifest.exists():
            return []
        findings = []
        for line in manifest.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "==" not in line:
                findings.append(
                    Finding(
                        module=self.name,
                        target=target.name,
                        description=f"Dependency '{line}' is not pinned",
                        severity="medium",
                        metadata={"manifest": str(manifest)},
                    )
                )
        return findings


@dataclass
class NodeDependencyAudit(AuditModule):
    """Highlight dependencies missing integrity metadata in package-lock files."""

    name: str = "node_dependency"
    lockfile_name: str = "package-lock.json"

    def collect(self, target: AuditTarget) -> Iterable[Finding]:
        lockfile = Path(target.path) / self.lockfile_name
        if not lockfile.exists():
            return []
        try:
            lock_data = json.loads(lockfile.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return [
                Finding(
                    module=self.name,
                    target=target.name,
                    description="package-lock.json is not valid JSON",
                    severity="high",
                    metadata={"lockfile": str(lockfile)},
                )
            ]
        dependencies = lock_data.get("dependencies", {})
        findings = []
        for package, details in dependencies.items():
            integrity = details.get("integrity")
            if not integrity:
                findings.append(
                    Finding(
                        module=self.name,
                        target=target.name,
                        description=f"Dependency '{package}' lacks integrity metadata",
                        severity="medium",
                        metadata={"lockfile": str(lockfile)},
                    )
                )
        return findings
