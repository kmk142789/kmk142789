"""Helpers for loading capability catalogues and state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .model import CapState, Capability

_DEFAULT_CATALOG_PATH = Path("manifest/capabilities.json")
_DEFAULT_STATE_PATH = Path("memory/capabilities_state.json")


def load_catalog(path: Path | None = None) -> Dict[str, Capability]:
    target = path or _DEFAULT_CATALOG_PATH
    if not target.exists():
        return {}
    data = json.loads(target.read_text(encoding="utf-8"))
    catalog: Dict[str, Capability] = {}
    for name, payload in data.items():
        if isinstance(payload, dict):
            payload.setdefault("name", name)
            catalog[name] = Capability.from_dict(payload)
    return catalog


def load_state(path: Path | None = None) -> CapState:
    target = path or _DEFAULT_STATE_PATH
    if not target.exists():
        return CapState()
    data = json.loads(target.read_text(encoding="utf-8"))
    provided = set(data.get("provided", [])) if isinstance(data, dict) else set()
    return CapState(provided=provided)


__all__ = ["load_catalog", "load_state"]
