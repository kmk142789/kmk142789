"""Sandboxed plugin protocol for Echo."""

from .manifest import load_manifest
from .sandbox import Sandbox
from .spec import PluginManifest, RPC

__all__ = ["PluginManifest", "RPC", "Sandbox", "load_manifest"]
