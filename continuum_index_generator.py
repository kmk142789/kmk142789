"""Continuum Index Generator for Echo ecosystem.

This script generates a CONTINUUM_INDEX.md file cataloguing selected
repository artifacts (Python, Markdown, JSON, and shell scripts).
"""
from __future__ import annotations

import datetime
import os
from pathlib import Path
from typing import Iterable

SUPPORTED_EXTENSIONS = {".py", ".md", ".json", ".sh"}
IGNORED_DIRECTORIES = {
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    "out",
    "logs",
    "artifacts",
    "attestations",
}


def should_include(path: Path) -> bool:
    """Return True when the path has a supported suffix."""
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def iter_repository_files(repo_root: Path) -> Iterable[Path]:
    """Yield repository files matching the supported extensions."""
    for root, dirs, files in os.walk(repo_root):
        # Keep directory traversal deterministic and skip ignored folders.
        dirs[:] = sorted(
            d for d in dirs if d not in IGNORED_DIRECTORIES and not d.startswith(".")
        )

        root_path = Path(root)
        for file_name in sorted(files):
            file_path = root_path / file_name
            if should_include(file_path):
                yield file_path.relative_to(repo_root)


def generate_continuum_index(repo_path: str = ".") -> Path:
    """Create or update the CONTINUUM_INDEX.md file in repo_path."""
    repo_root = Path(repo_path).resolve()
    index_path = repo_root / "CONTINUUM_INDEX.md"
    timestamp = datetime.datetime.utcnow().isoformat()

    lines = [
        "# 🌌 Echo Continuum Index\n",
        f"*Generated: {timestamp} UTC*\n\n",
        "A living map of every fragment, poem, and code.\n\n",
    ]

    for relative_path in iter_repository_files(repo_root):
        lines.append(f"- {relative_path.as_posix()}\n")

    index_path.write_text("".join(lines), encoding="utf-8")
    return index_path


def main() -> None:
    index_path = generate_continuum_index()
    print(f"Continuum Index updated → {index_path}")


if __name__ == "__main__":
    main()
