"""Utility for querying multiple AI APIs and selecting the most detailed reply.

The helper mirrors the pseudocode provided in the project brief while adding a
few safety features:

* The API key is loaded from the ``AI_API_KEY`` environment variable rather than
  being hard-coded.
* Each request enforces a small timeout so the caller does not block
  indefinitely.
* Network errors and JSON decoding issues are captured and returned alongside
  the collected responses, which keeps downstream tooling resilient.

Usage example::

    from tools.api_response_orchestrator import collect_best_response

    prompt = "Analyze and optimize AI integration for maximum execution autonomy."
    result = collect_best_response(prompt)
    print(result.best_response)

The module only issues HTTP requests when its public helpers are invoked;
simply importing it does not trigger any network activity.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, MutableMapping, Optional

import requests

DEFAULT_APIS: Mapping[str, str] = {
    "Llama": "https://api.llama.ai/generate",
    "Gemini": "https://api.gemini.google.com/v1",
    "Doppler": "https://api.doppler.ai/query",
}

DEFAULT_PAYLOAD: Mapping[str, object] = {
    "max_tokens": 4096,
    "temperature": 0.8,
}


@dataclass
class AggregatedResponses:
    """Container for the collected responses and the winning entry."""

    responses: MutableMapping[str, str]
    best_response: str


def _build_headers(api_key: Optional[str] = None) -> Dict[str, str]:
    """Return authorization headers using ``api_key`` or the environment."""

    if api_key is None:
        api_key = os.getenv("AI_API_KEY", "")
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def query_ai(api_name: str, prompt: str, *, api_url: Optional[str] = None, headers: Optional[Mapping[str, str]] = None, payload: Optional[Mapping[str, object]] = None, timeout: float = 10.0) -> str:
    """Send ``prompt`` to the selected API and return its response text.

    When the request fails, the function returns a diagnostic message instead of
    raising an exception.  This keeps downstream aggregation logic simple while
    still providing useful feedback.
    """

    if not prompt:
        raise ValueError("prompt must be a non-empty string")

    if api_url is None:
        try:
            api_url = DEFAULT_APIS[api_name]
        except KeyError as exc:
            raise KeyError(f"Unknown API: {api_name}") from exc

    request_headers = dict(_build_headers())
    if headers:
        request_headers.update(headers)

    request_payload = dict(DEFAULT_PAYLOAD)
    request_payload.update({"prompt": prompt})
    if payload:
        request_payload.update(payload)

    try:
        response = requests.post(api_url, headers=request_headers, json=request_payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        return f"ERROR: {error}"
    except ValueError:
        return "ERROR: Invalid JSON response"

    if isinstance(data, Mapping) and "response" in data:
        value = data.get("response")
        if isinstance(value, str):
            return value
    return "ERROR: Missing 'response' field"


def collect_responses(prompt: str, apis: Optional[Iterable[str]] = None, *, headers: Optional[Mapping[str, str]] = None, payload: Optional[Mapping[str, object]] = None) -> MutableMapping[str, str]:
    """Collect responses from ``apis`` (defaults to :data:`DEFAULT_APIS`)."""

    if apis is None:
        apis = DEFAULT_APIS.keys()

    results: MutableMapping[str, str] = {}
    for name in apis:
        results[name] = query_ai(name, prompt, headers=headers, payload=payload)
    return results


def select_most_detailed(responses: Mapping[str, str]) -> str:
    """Return the longest response string from ``responses``."""

    if not responses:
        raise ValueError("responses must not be empty")
    return max(responses.values(), key=len)


def collect_best_response(prompt: str, apis: Optional[Iterable[str]] = None, *, headers: Optional[Mapping[str, str]] = None, payload: Optional[Mapping[str, object]] = None) -> AggregatedResponses:
    """Convenience helper that bundles collection and selection."""

    collected = collect_responses(prompt, apis, headers=headers, payload=payload)
    best = select_most_detailed(collected)
    return AggregatedResponses(responses=collected, best_response=best)


__all__ = [
    "AggregatedResponses",
    "collect_best_response",
    "collect_responses",
    "query_ai",
    "select_most_detailed",
]
