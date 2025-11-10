"""Generate a comprehensive repository inventory.

Historically the continuum index only catalogued a handful of file
extensions which meant that large swaths of the repository never showed up
in the consolidated map.  The helper now leans on ``git ls-files`` so every
tracked artifact — regardless of extension — is included in the generated
``CONTINUUM_INDEX.md``.  When ``git`` is unavailable the previous directory
walk fallback is still used so downstream tooling continues to work in
minimal environments.
"""
from __future__ import annotations

import datetime
import os
import subprocess
from pathlib import Path
from typing import Iterable, Sequence

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


def iter_repository_files(repo_root: Path) -> Iterable[Path]:
    """Yield repository files tracked in the repository.

    ``git ls-files`` provides an authoritative list of tracked artifacts.
    We prefer it when available so the resulting index reflects the same
    files that developers see in version control.  When ``git`` is not
    present (for example in a constrained execution environment) we fall
    back to walking the directory tree and applying a minimal ignore list.
    """

    tracked = _git_tracked_paths(repo_root)
    if tracked:
        for relative_path in tracked:
            yield relative_path
        return

    # Fallback path: mirror the original behaviour so environments without
    # Git still produce a deterministic inventory.
    for root, dirs, files in os.walk(repo_root):
        # Keep directory traversal deterministic and skip ignored folders.
        dirs[:] = sorted(
            d for d in dirs if d not in IGNORED_DIRECTORIES and not d.startswith(".")
        )

        root_path = Path(root)
        for file_name in sorted(files):
            file_path = root_path / file_name
            yield file_path.relative_to(repo_root)


def _git_tracked_paths(repo_root: Path) -> Sequence[Path]:
    """Return tracked repository paths using ``git ls-files`` when possible."""

    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "-z"],
            check=True,
            capture_output=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ()

    paths: list[Path] = []
    entries = result.stdout.decode("utf-8", "surrogateescape").split("\0")
    for entry in entries:
        stripped = entry.strip()
        if not stripped:
            continue
        paths.append(Path(stripped))
    paths.sort()
    return tuple(paths)


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
