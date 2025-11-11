"""Configuration utilities for the vault API."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from vault_config.loader import ConfigLoader

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "config.v2.json"

_loader = ConfigLoader()


def load_config(path: str | os.PathLike[str] | None = None) -> Dict[str, Any]:
    """Load and validate configuration using the shared loader."""

    target = Path(path) if path else DEFAULT_CONFIG_PATH
    return _loader.load(target)


def latest_version() -> int:
    return _loader.current_version
