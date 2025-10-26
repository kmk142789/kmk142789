#!/usr/bin/env python3
"""CLI helper for signing EchoClaim/v1 payloads via skeleton keys."""

from __future__ import annotations

from skeleton_key_core import claim_cli


def main() -> int:
    return claim_cli()


if __name__ == "__main__":  # pragma: no cover - convenience entry point
    raise SystemExit(main())
