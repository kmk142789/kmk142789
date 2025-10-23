"""Very small subset of :mod:`httpx` used in the tests.

The production project relies on httpx for HTTP communication, but the kata
runtime does not bundle the dependency.  The tests only need a ``Client`` class
that can be instantiated and used as a context manager; network calls are
stubbed out.  The stub intentionally raises ``RuntimeError`` if a real request
is attempted so it fails loudly during development.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass
class Response:
    status_code: int
    _json: Any
    _text: str

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 400

    def json(self) -> Any:
        if isinstance(self._json, Exception):
            raise self._json
        return self._json

    @property
    def text(self) -> str:
        return self._text


class Client:
    def __init__(self, *_, timeout: float | None = None, **__) -> None:
        self.timeout = timeout

    # Context-manager helpers -------------------------------------------------
    def __enter__(self) -> "Client":  # pragma: no cover - trivial
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        self.close()

    def close(self) -> None:
        pass

    # HTTP verbs ---------------------------------------------------------------
    def post(
        self,
        url: str,
        *,
        json: Any | None = None,
        headers: Mapping[str, str] | None = None,
        auth: Any | None = None,
        timeout: float | None = None,
    ) -> Response:
        raise RuntimeError("httpx stub cannot perform network requests")


__all__ = ["Client", "Response"]
