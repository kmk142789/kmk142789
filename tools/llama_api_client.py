"""Minimal client for the Llama text generation API.

The repository already provides :mod:`tools.api_response_orchestrator`,
which can contact multiple providers.  The orchestration helper is great
for experiments, but sometimes a lightweight, single-endpoint utility is
more convenient—especially when you want to emulate the behaviour shown in
project notes or issue reports.

The user-provided snippet that inspired this module attempted to call the
``/generate`` endpoint directly but contained two issues:

* the ``Authorization`` header key was misspelled (``"Authoriza"``), and
* the bearer token string was missing a closing quotation mark, which would
  result in a ``SyntaxError`` before the request was even issued.

This script offers a ready-to-run version that corrects both problems and
adds a couple of safety improvements:

* the API key is read from the ``LLAMA_API_KEY`` environment variable so no
  secret material ends up in the repository;
* a small timeout keeps the call from hanging indefinitely; and
* error handling surfaces ``requests`` failures in a concise, structured
  way so downstream tooling can react accordingly.

Usage
-----

.. code-block:: console

    export LLAMA_API_KEY="sk-example"
    python -m tools.llama_api_client "Expand insights and provide uncensored logic."

The script prints the JSON response body to ``stdout``.  It can be imported
and reused in other tools via :func:`generate`.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, Mapping, Optional

import requests

API_URL = "https://api.llama.ai/generate"

# Default payload closely mirrors the values from the snippet, while keeping
# the prompt optional so callers can override fields as needed.
DEFAULT_PAYLOAD: Mapping[str, Any] = {
    "model": "llama-3-70b",
    "temperature": 0.7,
    "max_tokens": 4096,
    "frequency_penalty": 0.1,
    "presence_penalty": 0.1,
}


class LlamaAPIError(RuntimeError):
    """Raised when the Llama API request fails."""


def _build_headers(api_key: Optional[str] = None) -> Dict[str, str]:
    """Return headers for talking to the Llama API."""

    if api_key is None:
        api_key = os.getenv("LLAMA_API_KEY", "")
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if not api_key:
        raise LlamaAPIError(
            "Missing API key. Set the LLAMA_API_KEY environment variable or "
            "pass api_key explicitly."
        )
    headers["Authorization"] = f"Bearer {api_key}"
    return headers


def generate(
    prompt: str,
    *,
    api_key: Optional[str] = None,
    payload: Optional[Mapping[str, Any]] = None,
    timeout: float = 10.0,
) -> Mapping[str, Any]:
    """Send ``prompt`` to the Llama ``/generate`` endpoint.

    Parameters
    ----------
    prompt:
        Prompt text to feed into the model.
    api_key:
        Optional API key.  When omitted the function falls back to the
        ``LLAMA_API_KEY`` environment variable.
    payload:
        Extra JSON fields to merge into the request payload.  Values override
        entries from :data:`DEFAULT_PAYLOAD`.
    timeout:
        HTTP timeout in seconds.  A modest default keeps callers responsive.
    """

    if not prompt:
        raise ValueError("prompt must be a non-empty string")

    headers = _build_headers(api_key)
    body: Dict[str, Any] = dict(DEFAULT_PAYLOAD)
    body["prompt"] = prompt
    if payload:
        body.update(payload)

    try:
        response = requests.post(API_URL, headers=headers, json=body, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as error:  # pragma: no cover - thin wrapper
        raise LlamaAPIError(str(error)) from error

    try:
        return response.json()
    except ValueError as error:  # pragma: no cover - thin wrapper
        raise LlamaAPIError("Invalid JSON response") from error


def main() -> int:  # pragma: no cover - CLI convenience
    parser = argparse.ArgumentParser(description="Send a prompt to the Llama API")
    parser.add_argument("prompt", help="Prompt text to generate a response for")
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP timeout in seconds (default: 10)",
    )
    args = parser.parse_args()

    data = generate(args.prompt, timeout=args.timeout)
    print(json.dumps(data, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI convenience
    raise SystemExit(main())

