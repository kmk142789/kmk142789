"""Phantom mode redacts sensitive fields for read-only reporting."""

from __future__ import annotations

from typing import Any


class PhantomReporter:
    """Utility that removes sensitive fields from payloads."""

    def __init__(self, *, forbidden: set[str] | None = None) -> None:
        self.forbidden = forbidden or {"signature", "seed", "raw_input", "raw_key"}

    def redact(self, payload: Any) -> Any:
        if isinstance(payload, dict):
            return {
                key: self.redact(value)
                for key, value in payload.items()
                if key not in self.forbidden
            }
        if isinstance(payload, list):
            return [self.redact(item) for item in payload]
        return payload


__all__ = ["PhantomReporter"]
