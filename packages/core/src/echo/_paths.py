"""Shared path helpers to locate the monorepo roots."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def repo_root() -> Path:
    """Return the repository root by scanning upwards for pyproject.toml."""

    for candidate in [PACKAGE_ROOT, *PACKAGE_ROOT.parents]:
        if (candidate / "pyproject.toml").exists():
            return candidate
    raise RuntimeError("Unable to locate repository root; pyproject.toml missing")


REPO_ROOT = repo_root()
DATA_ROOT = REPO_ROOT / "data"
DOCS_ROOT = REPO_ROOT / "docs"
SCHEMA_ROOT = REPO_ROOT / "schema"
MANIFEST_ROOT = REPO_ROOT / "manifest"
