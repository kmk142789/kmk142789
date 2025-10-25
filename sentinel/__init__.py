"""Sentinel continuous verification and drift remediation package.

This module exposes helper factories used by the new Sentinel command line
utilities.  The package is intentionally self-contained so that the utilities
can be executed directly via ``python -m sentinel.<module>`` without requiring
installation.
"""

from __future__ import annotations

from importlib import metadata


def __getattr__(name: str) -> str:
    """Provide an ad-hoc ``__version__`` attribute.

    The project already declares its canonical version in ``pyproject.toml``
    for packaging purposes.  Importing ``sentinel`` should not fail when the
    metadata is unavailable (for example during editable development), so the
    lookup gracefully falls back to ``"0.0.0"``.
    """

    if name == "__version__":
        try:
            return metadata.version("echo-evolver")
        except metadata.PackageNotFoundError:
            return "0.0.0"
    raise AttributeError(name)


__all__ = ["__version__"]

