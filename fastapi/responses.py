"""Subset of FastAPI response helpers used in the tests."""

from __future__ import annotations

from . import Response


class HTMLResponse(Response):
    def __init__(self, content: str, status_code: int = 200, headers: dict[str, str] | None = None) -> None:
        super().__init__(content=content, status_code=status_code, media_type="text/html", headers=headers)


__all__ = ["HTMLResponse"]
