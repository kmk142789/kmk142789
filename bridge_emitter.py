#!/usr/bin/env python3
"""Command line entry point for :mod:`echo.bridge_emitter`."""

from __future__ import annotations

from echo.bridge_emitter import main as _package_main

__all__ = ["main"]


def main() -> int:  # pragma: no cover - thin CLI wrapper
    return _package_main()


if __name__ == "__main__":  # pragma: no cover - command line entry point
    raise SystemExit(main())
