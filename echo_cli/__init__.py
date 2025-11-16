"""Typer-based command line interface for Puzzle Lab."""

from importlib import import_module
from typing import Any

__all__ = ["app", "main"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        module = import_module(".main", __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(name)
