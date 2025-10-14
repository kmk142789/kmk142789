"""Configuration loader for Echo Meta Agent."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import dotenv_values


class Config:
    """Configuration helper that merges .env and YAML config."""

    def __init__(self) -> None:
        self._values: Dict[str, Any] = {}
        self._load_env()
        self._load_yaml()

    def _load_env(self) -> None:
        env_path = Path(".env")
        if env_path.exists():
            self._values.update(dotenv_values(env_path))
        else:
            # Fallback to environment variables when .env is absent.
            self._values.update({key: value for key, value in os.environ.items() if key.startswith("ECHO_")})

    def _load_yaml(self) -> None:
        yaml_path = Path(os.getenv("ECHO_META_AGENT_CONFIG", "echo_meta_agent.yaml"))
        if yaml_path.exists():
            with yaml_path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
            if isinstance(data, dict):
                self._values.update(data)

    def get(self, key: str, default: Any | None = None) -> Any | None:
        """Return the value associated with *key*, defaulting when missing."""

        return self._values.get(key, default)


_config = Config()


def get(key: str, default: Any | None = None) -> Any | None:
    """Convenience module level getter."""

    return _config.get(key, default)


__all__ = ["get", "Config"]
