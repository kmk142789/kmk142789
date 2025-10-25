"""HTTP adapter used for outward signaling."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional
from urllib import request


@dataclass
class HTTPResponse:
    status: int
    body: str


class HTTPAdapter:
    """Very small HTTP client based on :mod:`urllib` to avoid dependencies."""

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def post(self, url: str, payload: Mapping[str, Any], headers: Optional[Mapping[str, str]] = None) -> HTTPResponse:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)
        with request.urlopen(req, timeout=self.timeout) as resp:
            text = resp.read().decode("utf-8")
            return HTTPResponse(status=resp.status, body=text)

