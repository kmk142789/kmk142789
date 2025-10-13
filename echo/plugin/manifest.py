"""Utilities for loading plugin manifests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None

from .spec import PluginManifest


def _load_yaml(path: Path) -> Dict[str, Any]:
    if yaml is not None:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
            if not isinstance(data, dict):
                raise ValueError("Manifest must be a mapping")
            return data

    # Fallback very small subset YAML parser
    result: Dict[str, Any] = {}
    capabilities: List[str] | None = None
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("-") and capabilities is not None:
                capabilities.append(line.lstrip("- "))
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if key == "capabilities":
                    capabilities = []
                    result[key] = capabilities
                else:
                    result[key] = value
    return result


def _load_json(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Manifest must be a mapping")
    return data


def load_manifest(path: str | Path) -> PluginManifest:
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)
    if manifest_path.suffix in {".yaml", ".yml"}:
        data = _load_yaml(manifest_path)
    else:
        data = _load_json(manifest_path)
    return PluginManifest(
        name=str(data.get("name")),
        version=str(data.get("version", "0.1.0")),
        capabilities=[str(cap) for cap in data.get("capabilities", [])],
        entrypoint=str(data.get("entrypoint")),
    )


__all__ = ["load_manifest"]
