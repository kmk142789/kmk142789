"""Git adapter for Dominion journaling."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class GitStatus:
    head: Optional[str]
    dirty: bool


class GitAdapter:
    """Surface-level Git metadata to embed inside receipts."""

    def __init__(self, root: Path | str = ".") -> None:
        self.root = Path(root).resolve()

    def _run(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.root,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()

    def status(self) -> GitStatus:
        head = self._run("rev-parse", "HEAD") or None
        dirty_output = self._run("status", "--porcelain")
        dirty = bool(dirty_output)
        return GitStatus(head=head, dirty=dirty)

