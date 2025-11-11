"""Configuration loader for Atlas OS."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

import yaml


DEFAULT_CONFIG_PATH = Path(os.environ.get("ATLAS_CONFIG", "config/atlas.yaml"))


@dataclass(slots=True)
class AtlasConfig:
    """Represents a deterministic configuration snapshot."""

    root: Path
    env: Dict[str, str]
    settings: Dict[str, Any]
    data_dir: Path = field(default_factory=lambda: Path("data"))

    def get(self, key: str, default: Any = None) -> Any:
        if key in self.env:
            return self.env[key]
        return self.settings.get(key, default)

    def require(self, key: str) -> Any:
        value = self.get(key)
        if value is None:
            raise KeyError(f"Missing required config value: {key}")
        return value

    @property
    def scheduler_db(self) -> Path:
        return self.root / Path(self.get("scheduler_db", "data/scheduler.db"))

    @property
    def storage_dir(self) -> Path:
        return self.root / Path(self.get("storage_dir", "data/storage"))

    @property
    def identity_cache(self) -> Path:
        return self.root / Path(self.get("identity_cache", "data/did_cache.json"))

    @property
    def metrics_host(self) -> str:
        return str(self.get("metrics_host", "0.0.0.0"))

    @property
    def metrics_port(self) -> int:
        return int(self.get("metrics_port", 9100))


def load_config(path: Path | None = None) -> AtlasConfig:
    """Load configuration from environment variables and atlas.yaml."""
    root = Path(os.environ.get("ATLAS_ROOT", Path.cwd()))
    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.is_absolute():
        config_path = root / config_path

    settings: Dict[str, Any] = {}
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
            if not isinstance(data, dict):
                raise ValueError("atlas.yaml must define a mapping")
            settings = data

    env = {
        key.removeprefix("ATLAS_"): value
        for key, value in os.environ.items()
        if key.startswith("ATLAS_")
    }

    data_dir = root / Path(env.get("DATA_DIR", settings.get("data_dir", "data")))
    data_dir.mkdir(parents=True, exist_ok=True)

    return AtlasConfig(root=root, env=env, settings=settings, data_dir=data_dir)


__all__ = ["AtlasConfig", "load_config"]
