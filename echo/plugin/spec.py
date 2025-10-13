"""Plugin protocol specification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class PluginManifest:
    name: str
    version: str
    capabilities: List[str]
    entrypoint: str


RPC: Dict[str, Dict[str, Any]] = {
    "echo.ping": {"params": [], "returns": "str"},
    "echo.capabilities": {"params": [], "returns": "list[str]"},
}

__all__ = ["PluginManifest", "RPC"]
