from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path
from typing import Any

from ..utils import Finding


class ArchiveProbe:
    name = "archive"

    def run(self, inventory: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        root = Path.cwd()
        for receipt in inventory.get("receipts", []):
            path = root / receipt["path"]
            if not path.exists() or not path.is_file():
                continue
            if path.suffix in {".zip"}:
                findings.append(self._check_zip(path))
            elif path.suffix in {".tar", ".tgz", ".tar.gz"}:
                findings.append(self._check_tar(path))
        return [finding for finding in findings if finding]

    def _check_zip(self, path: Path) -> Finding:
        try:
            with zipfile.ZipFile(path) as zf:
                corrupt = zf.testzip()
                if corrupt:
                    return Finding(
                        probe=self.name,
                        subject=str(path),
                        status="error",
                        message=f"Corrupt zip entry: {corrupt}",
                        data={"path": str(path)},
                    )
        except zipfile.BadZipFile as exc:
            return Finding(
                probe=self.name,
                subject=str(path),
                status="error",
                message="Invalid zip archive",
                data={"error": str(exc)},
            )
        return Finding(
            probe=self.name,
            subject=str(path),
            status="ok",
            message="Zip archive verified",
            data={},
        )

    def _check_tar(self, path: Path) -> Finding:
        try:
            mode = "r:gz" if path.suffixes[-2:] == [".tar", ".gz"] or path.suffix == ".tgz" else "r"
            with tarfile.open(path, mode) as tf:
                for member in tf.getmembers():
                    if member.isfile() and member.size < 0:
                        raise tarfile.TarError(f"Corrupt member: {member.name}")
        except (tarfile.TarError, FileNotFoundError) as exc:
            return Finding(
                probe=self.name,
                subject=str(path),
                status="error",
                message="Invalid tar archive",
                data={"error": str(exc)},
            )
        return Finding(
            probe=self.name,
            subject=str(path),
            status="ok",
            message="Tar archive verified",
            data={},
        )


__all__ = ["ArchiveProbe"]

