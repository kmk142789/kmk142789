"""Configuration helpers for the Assistant Kit."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts" / "akit"
STATE_FILE = ARTIFACT_DIR / "state.json"
REPORT_FILE = ARTIFACT_DIR / "report.json"
DEFAULT_PLAN_FILE = ARTIFACT_DIR / "plan-latest.json"
DEFAULT_SNAPSHOT_DIR = ARTIFACT_DIR
APPROVAL_ENV_VAR = "AKIT_APPROVED"
DEFAULT_ARTIFACT_LIMIT = 5

ALLOWED_PREFIXES = (
    REPO_ROOT / "artifacts",
    REPO_ROOT / "docs",
    REPO_ROOT / "echo",
    REPO_ROOT / "modules",
)


@dataclass(slots=True, frozen=True)
class AKitConfig:
    """Runtime configuration derived from environment variables."""

    artifact_limit: int
    approval_env_var: str
    allowed_prefixes: List[Path]

    @property
    def approval_granted(self) -> bool:
        return os.getenv(self.approval_env_var, "").lower() in {"1", "true", "yes", "y"}


def load_config(*, artifact_limit: int | None = None) -> AKitConfig:
    limit = artifact_limit if artifact_limit is not None else DEFAULT_ARTIFACT_LIMIT
    return AKitConfig(
        artifact_limit=limit,
        approval_env_var=APPROVAL_ENV_VAR,
        allowed_prefixes=[Path(prefix) for prefix in ALLOWED_PREFIXES],
    )


def ensure_directories() -> None:
    """Create directories used by the Assistant Kit."""

    for path in (ARTIFACT_DIR,):
        path.mkdir(parents=True, exist_ok=True)


def is_path_allowed(path: Path, *, allowed: Iterable[Path] | None = None) -> bool:
    """Return ``True`` if ``path`` is within one of the allowed prefixes."""

    prefixes = list(allowed or ALLOWED_PREFIXES)
    resolved = path.resolve()
    for prefix in prefixes:
        try:
            resolved.relative_to(prefix.resolve())
            return True
        except ValueError:
            continue
    return False
