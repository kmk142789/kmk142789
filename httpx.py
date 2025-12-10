"""Very small subset of :mod:`httpx` used in the tests.

The production project relies on httpx for HTTP communication, but the kata
runtime does not bundle the dependency.  The tests primarily need ``Client`` and
``AsyncClient`` classes that can be instantiated and used as context managers;
network calls are stubbed out.  The stub intentionally raises ``RuntimeError``
if a real request is attempted so it fails loudly during development, but
callers may supply ``mock_responses`` to return pre-baked :class:`Response`
instances instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping


@dataclass
class Response:
    status_code: int
    _json: Any
    _text: str

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 400

    def raise_for_status(self) -> None:
        """Raise :class:`HTTPStatusError` when the response is not successful."""

        if not self.is_success:
            raise HTTPStatusError(self.status_code, response=self)

    def json(self) -> Any:
        if isinstance(self._json, Exception):
            raise self._json
        return self._json

    @property
    def text(self) -> str:
        return self._text


class Client:
    def __init__(
        self,
        *_,
        timeout: float | None = None,
        mock_responses: Mapping[str, Response] | None = None,
        **__,
    ) -> None:
        self.timeout = timeout
        self._mock_responses: MutableMapping[str, Response] = (
            dict(mock_responses) if mock_responses else {}
        )

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
        if url in self._mock_responses:
            return self._mock_responses[url]
        raise RuntimeError("httpx stub cannot perform network requests")

    def get(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        auth: Any | None = None,
        timeout: float | None = None,
    ) -> Response:
        if url in self._mock_responses:
            return self._mock_responses[url]
        raise RuntimeError("httpx stub cannot perform network requests")


class AsyncClient:
    def __init__(
        self,
        *_,
        timeout: float | None = None,
        mock_responses: Mapping[str, Response] | None = None,
        **__,
    ) -> None:
        self.timeout = timeout
        self._mock_responses: MutableMapping[str, Response] = (
            dict(mock_responses) if mock_responses else {}
        )

    async def __aenter__(self) -> "AsyncClient":  # pragma: no cover - trivial
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        await self.aclose()

    async def aclose(self) -> None:
        pass

    async def get(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        auth: Any | None = None,
        timeout: float | None = None,
    ) -> Response:
        if url in self._mock_responses:
            return self._mock_responses[url]
        raise RuntimeError("httpx stub cannot perform network requests")

    async def post(
        self,
        url: str,
        *,
        json: Any | None = None,
        headers: Mapping[str, str] | None = None,
        auth: Any | None = None,
        timeout: float | None = None,
    ) -> Response:
        if url in self._mock_responses:
            return self._mock_responses[url]
        raise RuntimeError("httpx stub cannot perform network requests")


class HTTPStatusError(RuntimeError):
    """Minimal stand-in for :class:`httpx.HTTPStatusError`."""

    def __init__(self, status_code: int, response: Response | None = None) -> None:
        super().__init__(f"HTTP request failed with status {status_code}")
        self.response = response
        self.status_code = status_code


__all__ = ["AsyncClient", "Client", "HTTPStatusError", "Response"]
