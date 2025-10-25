"""Adapter registry and dependency wiring."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .adapters import ArchiveAdapter, FileSystemAdapter, GitAdapter, HTTPAdapter


@dataclass
class AdapterRegistry:
    root: Path = field(default_factory=lambda: Path(".").resolve())

    def filesystem(self) -> FileSystemAdapter:
        return FileSystemAdapter(self.root)

    def git(self) -> GitAdapter:
        return GitAdapter(self.root)

    def http(self) -> HTTPAdapter:
        return HTTPAdapter()

    def archive(self) -> ArchiveAdapter:
        return ArchiveAdapter(self.root)

