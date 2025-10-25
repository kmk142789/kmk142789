from __future__ import annotations

import json
from pathlib import Path

from dominion.adapters import ArchiveAdapter, FileSystemAdapter


def test_filesystem_snapshot_and_restore(tmp_path: Path) -> None:
    fs = FileSystemAdapter(tmp_path)
    target = tmp_path / "example.txt"
    target.write_text("original", encoding="utf-8")
    snapshot = fs.snapshot(target)

    fs.write_text(target, "modified")
    assert target.read_text(encoding="utf-8") == "modified"

    fs.restore(snapshot)
    assert target.read_text(encoding="utf-8") == "original"


def test_archive_adapter_creates_signature(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "data.txt").write_text("payload", encoding="utf-8")

    adapter = ArchiveAdapter(tmp_path)
    receipt = adapter.create_archive(source, tmp_path / "out", name="demo")

    assert receipt.archive_path.exists()
    signature_data = json.loads(receipt.signature_path.read_text(encoding="utf-8"))
    assert signature_data["sha256"] == receipt.digest
    assert signature_data["archive"] == receipt.archive_path.name
