"""Lightweight Python namespace for repository-local utilities.

This module coexists with historical C++ sources and enables imports such
as ``src.telemetry`` within the test environment.
"""

from .aurora_chronicle import ChroniclePrompt, compose_chronicle, demo as chronicle_demo

__all__ = ["ChroniclePrompt", "compose_chronicle", "chronicle_demo"]
