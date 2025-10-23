"""Utility helpers compatible with the interfaces used in tests."""

from __future__ import annotations

import os


def random(size: int) -> bytes:
    return os.urandom(size)


__all__ = ["random"]
