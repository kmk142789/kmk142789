"""Subset of FastAPI response helpers used in the tests."""

from __future__ import annotations

import json
from typing import Any

from . import Response


class HTMLResponse(Response):
    def __init__(self, content: str, status_code: int = 200, headers: dict[str, str] | None = None) -> None:
        super().__init__(content=content, status_code=status_code, media_type="text/html", headers=headers)


class JSONResponse(Response):
    """Minimal JSON response that mirrors FastAPI's behaviour for tests."""

    def __init__(self, content: Any, status_code: int = 200, headers: dict[str, str] | None = None) -> None:
        body = json.dumps(content, ensure_ascii=False)
        super().__init__(content=body, status_code=status_code, media_type="application/json", headers=headers)


__all__ = ["HTMLResponse", "JSONResponse"]
