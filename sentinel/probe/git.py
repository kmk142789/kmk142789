from __future__ import annotations

import subprocess
from typing import Any

from ..utils import Finding


class GitProbe:
    name = "git"

    def run(self, inventory: dict[str, Any]) -> list[Finding]:  # noqa: ARG002 - inventory future use
        findings: list[Finding] = []

        commit = self._run_git(["rev-parse", "HEAD"])
        if commit:
            findings.append(
                Finding(
                    probe=self.name,
                    subject="repository",
                    status="ok",
                    message="Repository HEAD located",
                    data={"commit": commit},
                )
            )
        else:
            findings.append(
                Finding(
                    probe=self.name,
                    subject="repository",
                    status="error",
                    message="Unable to resolve repository HEAD",
                    data={},
                )
            )

        status = self._run_git(["status", "--porcelain"])
        if status:
            findings.append(
                Finding(
                    probe=self.name,
                    subject="repository",
                    status="warning",
                    message="Working tree has uncommitted changes",
                    data={"entries": status.splitlines()},
                )
            )
        else:
            findings.append(
                Finding(
                    probe=self.name,
                    subject="repository",
                    status="ok",
                    message="Working tree clean",
                    data={},
                )
            )
        return findings

    @staticmethod
    def _run_git(args: list[str]) -> str:
        try:
            result = subprocess.run(["git", *args], check=True, capture_output=True, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ""
        return result.stdout.strip()


__all__ = ["GitProbe"]

