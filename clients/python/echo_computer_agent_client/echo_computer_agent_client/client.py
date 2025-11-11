from __future__ import annotations

from typing import Any, Mapping, MutableMapping

import requests

from .types import ChatRequest, ChatResponse, FunctionListResponse


class EchoComputerAgentClient:
    """Requests-based client for the Echo Computer Agent API."""

    def __init__(
        self,
        base_url: str,
        *,
        session: requests.Session | None = None,
        default_headers: Mapping[str, str] | None = None,
    ) -> None:
        self._base_url = base_url.rstrip('/')
        self._session = session or requests.Session()
        self._headers: MutableMapping[str, str] = dict(default_headers or {})

    def close(self) -> None:
        """Close the underlying HTTP session."""

        self._session.close()

    def list_functions(self, *, timeout: float | None = None) -> FunctionListResponse:
        """Return the available function specifications."""

        response = self._session.get(
            f"{self._base_url}/functions",
            headers=dict(self._headers),
            timeout=timeout,
        )
        response.raise_for_status()
        payload: FunctionListResponse = response.json()  # type: ignore[assignment]
        return payload

    def chat(
        self,
        message: str,
        *,
        inputs: Mapping[str, Any] | None = None,
        execute: bool | None = None,
        timeout: float | None = None,
    ) -> ChatResponse:
        """Send a chat request to the agent and return the structured response."""

        payload: ChatRequest = {"message": message}
        if inputs is not None:
            payload["inputs"] = dict(inputs)
        if execute is not None:
            payload["execute"] = execute
        headers = {"Content-Type": "application/json", **self._headers}
        response = self._session.post(
            f"{self._base_url}/chat",
            json=payload,
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
        chat_response: ChatResponse = response.json()  # type: ignore[assignment]
        return chat_response
