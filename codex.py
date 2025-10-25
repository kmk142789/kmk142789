"""Alias module exposing :mod:`packages.core.src.codex` at the top level."""
import importlib
import sys

_core = importlib.import_module("packages.core.src.codex")
sys.modules[__name__] = _core
