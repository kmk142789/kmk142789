"""Compatibility shim for Astral Compression Engine.

The Astral Compression Engine now lives in the core :mod:`echo` package. Importing
via :mod:`src.astral_compression_engine` remains supported for callers that have
not yet migrated.
"""

from echo.astral_compression_engine import *  # noqa: F401,F403
