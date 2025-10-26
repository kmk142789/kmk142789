#!/usr/bin/env python3
"""CLI wrapper for deriving Echo skeleton keys."""

from __future__ import annotations

from skeleton_key_core import derive_cli


def main() -> int:
    return derive_cli()


if __name__ == "__main__":  # pragma: no cover - convenience entry point
    raise SystemExit(main())
