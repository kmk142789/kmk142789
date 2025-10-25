from __future__ import annotations

import ssl
import urllib.request
from typing import Any

from ..utils import Finding


class HttpProbe:
    name = "http"

    def __init__(self, timeout: float = 5.0) -> None:
        self.timeout = timeout

    def run(self, inventory: dict[str, Any]) -> list[Finding]:
        endpoints = inventory.get("signals", {}).get("http_endpoints", [])
        findings: list[Finding] = []
        for endpoint in endpoints:
            status, data = self._check_endpoint(endpoint)
            findings.append(
                Finding(
                    probe=self.name,
                    subject=endpoint,
                    status=status,
                    message=data.get("message", ""),
                    data=data,
                )
            )
        return findings

    def _check_endpoint(self, endpoint: str) -> tuple[str, dict[str, Any]]:
        request = urllib.request.Request(endpoint, method="HEAD")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout, context=ssl.create_default_context()) as response:
                return "ok", {"status": response.status, "message": "Endpoint reachable"}
        except urllib.error.HTTPError as exc:  # type: ignore[attr-defined]
            return "warning", {"status": exc.code, "message": "HTTP error", "reason": exc.reason}
        except Exception as exc:  # pragma: no cover - network failures are environment-specific
            return "warning", {"message": f"{type(exc).__name__}: {exc}"}


__all__ = ["HttpProbe"]

