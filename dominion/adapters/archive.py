"""Archive helper for packaging Dominion artifacts."""

from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class ArchiveReceipt:
    archive_path: Path
    signature_path: Path
    digest: str


class ArchiveAdapter:
    """Bundle directories into deterministic archives with SHA-256 signatures."""

    def __init__(self, root: Path | str = ".") -> None:
        self.root = Path(root).resolve()

    def _iter_files(self, directory: Path) -> Iterable[Path]:
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                yield path

    def create_archive(self, source: Path | str, out_dir: Path | str, *, name: str) -> ArchiveReceipt:
        source_path = Path(source).resolve()
        out_path = Path(out_dir).resolve()
        out_path.mkdir(parents=True, exist_ok=True)
        archive_path = out_path / f"{name}.zip"
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for file_path in self._iter_files(source_path):
                zf.write(file_path, arcname=file_path.relative_to(source_path))
        digest = self._digest_file(archive_path)
        signature_path = archive_path.with_suffix(".zip.sig")
        signature_payload = {"sha256": digest, "archive": archive_path.name}
        signature_path.write_text(json.dumps(signature_payload, indent=2), encoding="utf-8")
        return ArchiveReceipt(archive_path=archive_path, signature_path=signature_path, digest=digest)

    def _digest_file(self, path: Path) -> str:
        sha = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                sha.update(chunk)
        return sha.hexdigest()

