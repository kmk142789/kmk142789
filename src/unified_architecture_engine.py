"""Compatibility shim for the Unified Architecture Engine.

The Unified Architecture Engine lives in the core :mod:`echo` package. This
shim keeps legacy imports such as :mod:`src.unified_architecture_engine`
working so downstream tools can access the latest blueprint builder without
needing to change their import paths.
"""

from echo.unified_architecture_engine import *  # noqa: F401,F403
