"""Alias module exposing :mod:`packages.core.src.codex` at the top level."""

from __future__ import annotations

import importlib
from types import ModuleType
from typing import Any

_core: ModuleType = importlib.import_module("packages.core.src.codex")
__all__ = getattr(_core, "__all__", [])  # type: ignore[assignment]


def __getattr__(name: str) -> Any:  # pragma: no cover - thin forwarding wrapper
    return getattr(_core, name)


def __dir__() -> list[str]:  # pragma: no cover - thin forwarding wrapper
    return sorted(set(dir(_core) + list(globals())))


def main(*args: Any, **kwargs: Any) -> Any:
    return getattr(_core, "main")(*args, **kwargs)
