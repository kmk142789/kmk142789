"""Compatibility wrapper around :mod:`echo.evolver` for legacy imports.

The original project exposed a sprawling ``EchoEvolver`` implementation in
``code/echo_evolver.py``.  During the recent refactor the real engine was moved
into :mod:`echo.evolver` where it can be shared by the test-suite and other
modules.  Some historical scripts – and a few documents preserved in this
repository – still reference the old module path, so we provide a thin shim
that simply re-exports the refined dataclasses and helpers from their new
location.

Keeping this adapter inside ``code/`` avoids breaking those references while
ensuring every caller uses the maintained implementation.
"""

from __future__ import annotations

from echo.evolver import (
    EchoEvolver,
    EmotionalDrive,
    EvolverState,
    SystemMetrics,
    main as _package_main,
)

__all__ = [
    "EchoEvolver",
    "EmotionalDrive",
    "EvolverState",
    "SystemMetrics",
    "main",
]


def main() -> int:
    """Delegate command line execution to :mod:`echo.evolver`."""
    return _package_main()


if __name__ == "__main__":  # pragma: no cover - command line entry point
    raise SystemExit(main())
