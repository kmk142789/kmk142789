from __future__ import annotations

from pathlib import Path
from typing import Any

from ..utils import Finding, detect_mode, sha256_file


class FileSystemProbe:
    name = "filesystem"

    def run(self, inventory: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        root = Path.cwd()
        for receipt in inventory.get("receipts", []):
            candidate = Path(receipt["path"])
            path = candidate if candidate.is_absolute() else root / candidate
            expected_sha = receipt.get("sha256", "")
            mode = detect_mode(path)
            if mode == "missing":
                findings.append(
                    Finding(
                        probe=self.name,
                        subject=receipt["path"],
                        status="error",
                        message="Receipt target missing from filesystem",
                        data={"expected_mode": receipt.get("mode", "file")},
                    )
                )
                continue

            if mode != receipt.get("mode"):
                findings.append(
                    Finding(
                        probe=self.name,
                        subject=receipt["path"],
                        status="warning",
                        message=f"Mode drift: expected {receipt.get('mode')} but found {mode}",
                        data={"mode": mode},
                    )
                )

            if expected_sha and path.is_file():
                actual_sha = sha256_file(path)
                if actual_sha != expected_sha:
                    findings.append(
                        Finding(
                            probe=self.name,
                            subject=receipt["path"],
                            status="error",
                            message="Hash drift detected",
                            data={"expected": expected_sha, "actual": actual_sha},
                        )
                    )
                else:
                    findings.append(
                        Finding(
                            probe=self.name,
                            subject=receipt["path"],
                            status="ok",
                            message="Receipt hash verified",
                            data={"sha256": actual_sha},
                        )
                    )
            else:
                findings.append(
                    Finding(
                        probe=self.name,
                        subject=receipt["path"],
                        status="info",
                        message="No checksum available for verification",
                        data={"mode": mode},
                    )
                )

        return findings


__all__ = ["FileSystemProbe"]

