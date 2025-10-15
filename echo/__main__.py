"""Module entry point for ``python -m echo``."""

from __future__ import annotations

from .cli import main


if __name__ == "__main__":  # pragma: no cover - module invocation
    raise SystemExit(main())

