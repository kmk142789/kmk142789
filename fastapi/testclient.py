"""Expose :class:`fastapi.TestClient` for ``from fastapi.testclient import TestClient`` imports."""

from __future__ import annotations

from . import TestClient

__all__ = ["TestClient"]
