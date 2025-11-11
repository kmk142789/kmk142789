#!/usr/bin/env python3
"""Synchronise configuration changelog entries with available config files."""

from __future__ import annotations

import sys
from pathlib import Path


def _bootstrap_path() -> None:
    root = Path(__file__).resolve().parents[2] / "src"
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


_bootstrap_path()

from vault_config.loader import ConfigLoader  # noqa: E402


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    configs = sorted((base_dir / "configs").glob("config.v*.*"))
    loader = ConfigLoader()
    for config_file in configs:
        loader.load(config_file)
    print(f"Changelog updated at {loader.changelog_path}")


if __name__ == "__main__":
    main()
