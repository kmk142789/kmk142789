"""Utility helpers for the Echo Atlas module."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path
from typing import Iterable


def slugify(*parts: str) -> str:
    """Return a deterministic, filesystem-friendly identifier."""

    raw = "::".join(part.strip().lower().replace(" ", "-") for part in parts if part)
    digest = sha1(raw.encode("utf-8")).hexdigest()[:10]
    compact = raw.replace("::", "-").replace("/", "-")
    compact = "-".join(p for p in compact.split("-") if p)
    return f"{compact}-{digest}" if compact else digest


def utcnow() -> str:
    """Return an ISO-8601 timestamp with timezone."""

    return datetime.now(tz=timezone.utc).isoformat()


def ensure_directory(path: Path) -> None:
    """Create a directory if it does not exist."""

    path.mkdir(parents=True, exist_ok=True)


def chunked(iterable: Iterable, size: int):
    """Yield fixed-size chunks from *iterable*."""

    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk
