"""Remedy planning and application helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RemedyAction:
    id: str
    subject: str
    description: str
    status: str = "pending"
    metadata: dict[str, Any] | None = None


__all__ = ["RemedyAction"]

