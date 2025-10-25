"""Structured logging utilities for Colossus."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
import json


@dataclass
class StructuredLogger:
    """Write NDJSON log lines for generator activity."""

    path: Path

    def emit(self, message: str, **fields: Any) -> None:
        payload: Dict[str, Any] = {"message": message, **fields}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.write("\n")


__all__ = ["StructuredLogger"]
