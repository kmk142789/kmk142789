"""Robust client utilities for coordinating multiple AI HTTP endpoints.

The original request script bundled with the repository attempted to call a
series of remote AI APIs using :mod:`requests`.  The script provided no
payloads, did not persist successful responses defensively, and crashed loudly
whenever a gateway returned a non-JSON payload.  The helpers in this module
offer a structured alternative that:

* normalises headers, authentication, and output directories;
* records every result – successful or not – in a lightweight dataclass; and
* gracefully handles exceptions and malformed responses without leaving the
  caller guessing what happened.

These utilities rely on :mod:`httpx`, which is already part of the project
dependencies, and are designed so that tests (or downstream code) can inject a
stub client when real network traffic is undesirable.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping

import httpx


@dataclass(slots=True)
class ApiCallResult:
    """Container describing the outcome of a single API invocation."""

    app: str
    status_code: int
    ok: bool
    payload: Any | None
    error: str | None
    output_path: Path | None = None
    response_text: str | None = None

    def __bool__(self) -> bool:  # pragma: no cover - trivial proxy
        return self.ok


class MultiAIClient:
    """Coordinate POST calls across a fleet of AI API endpoints.

    Parameters
    ----------
    endpoints:
        Mapping of application identifiers to absolute endpoint URLs.
    output_dir:
        Directory where successful JSON responses should be written.  The
        directory is created automatically if it does not already exist.
    auth:
        Optional basic-auth credential tuple passed directly to ``httpx``.
    headers:
        Additional HTTP headers that should be merged with the default JSON
        content type.
    client:
        Optional pre-configured :class:`httpx.Client`.  Tests can use this hook
        to provide a stub.  When omitted the client is created internally and
        closed automatically via :meth:`close`.
    """

    def __init__(
        self,
        endpoints: Mapping[str, str],
        *,
        output_dir: Path | str = Path("echo_output"),
        auth: tuple[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        if not endpoints:
            raise ValueError("endpoints mapping must not be empty")

        self.endpoints: MutableMapping[str, str] = dict(endpoints)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.auth = auth

        merged_headers = {"content-type": "application/json"}
        if headers:
            merged_headers.update(headers)
        self.headers = merged_headers

        self._client = client or httpx.Client()
        self._owns_client = client is None

    # ------------------------------------------------------------------
    # Lifecycle management
    # ------------------------------------------------------------------
    def close(self) -> None:
        """Close the underlying client if this instance created it."""

        if self._owns_client:
            self._client.close()

    # Context manager helpers keep resource management simple for callers.
    def __enter__(self) -> "MultiAIClient":  # pragma: no cover - trivial
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        self.close()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def invoke(
        self,
        app: str,
        *,
        payload: Mapping[str, Any] | None = None,
        timeout: float | None = None,
    ) -> ApiCallResult:
        """Call ``app``'s endpoint and return a structured result."""

        if app not in self.endpoints:
            raise KeyError(f"Unknown application '{app}'")

        url = self.endpoints[app]
        json_payload: Mapping[str, Any] = payload or {}

        try:
            response = self._client.post(
                url,
                json=json_payload,
                headers=self.headers,
                auth=self.auth,
                timeout=timeout,
            )
        except Exception as exc:  # pragma: no cover - exercised via tests
            return ApiCallResult(
                app=app,
                status_code=0,
                ok=False,
                payload=None,
                error=str(exc),
            )

        try:
            payload_data = response.json()
            body_text = json.dumps(payload_data, indent=2, ensure_ascii=False)
            parse_error: str | None = None
        except ValueError:
            payload_data = None
            body_text = response.text
            parse_error = "Response did not contain valid JSON"

        result = ApiCallResult(
            app=app,
            status_code=response.status_code,
            ok=response.is_success and parse_error is None,
            payload=payload_data,
            error=parse_error,
            response_text=body_text,
        )

        if result.ok and body_text is not None:
            output_path = self.output_dir / f"{app}.json"
            output_path.write_text(body_text, encoding="utf-8")
            result.output_path = output_path
        elif not result.ok:
            body_excerpt = (body_text or "").strip()
            snippet = body_excerpt[:200]
            if len(body_excerpt) > 200:
                snippet += "…"
            if parse_error is None:
                result.error = (
                    f"HTTP {response.status_code}: {snippet or 'No response body'}"
                )
            else:
                detail = snippet or parse_error
                result.error = f"HTTP {response.status_code}: {detail}"

        return result

    def invoke_all(
        self,
        *,
        base_payload: Mapping[str, Any] | None = None,
        per_app_payloads: Mapping[str, Mapping[str, Any]] | None = None,
        timeout: float | None = None,
    ) -> list[ApiCallResult]:
        """Invoke every configured endpoint with sensible payload defaults."""

        results: list[ApiCallResult] = []
        for app in self.endpoints:
            payload = None
            if per_app_payloads and app in per_app_payloads:
                payload = per_app_payloads[app]
            elif base_payload is not None:
                payload = base_payload
            results.append(self.invoke(app, payload=payload, timeout=timeout))
        return results


def summarise_results(results: Iterable[ApiCallResult]) -> str:
    """Build a concise multi-line summary for CLI feedback."""

    lines = []
    for result in results:
        status = "ok" if result.ok else "error"
        detail = (
            f"saved to {result.output_path}" if result.ok and result.output_path else result.error
        )
        lines.append(f"{result.app}: {status} ({detail})")
    return "\n".join(lines)


__all__ = ["ApiCallResult", "MultiAIClient", "summarise_results"]

