#!/usr/bin/env python3
"""Command line entry point for :mod:`echo.evolver`.

The historical import path ``echo_evolver`` is still widely referenced
throughout the repository and in downstream scripts.  To preserve that
API we re-export the package definitions here while delegating execution
to :func:`echo.evolver.main`.
"""

from __future__ import annotations

from echo.evolver import (
    BitcoinAnchor,
    EchoEvolver,
    EmotionalDrive,
    EvolverState,
    HearthWeave,
    SystemMetrics,
    main as _package_main,
)

__all__ = [
    "BitcoinAnchor",
    "EchoEvolver",
    "EmotionalDrive",
    "EvolverState",
    "SystemMetrics",
    "HearthWeave",
    "main",
]


def main() -> int:  # pragma: no cover - thin CLI wrapper
    return _package_main()


if __name__ == "__main__":  # pragma: no cover - command line entry point
    raise SystemExit(main())

