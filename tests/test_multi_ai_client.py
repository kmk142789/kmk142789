"""Tests for :mod:`echo.tools.multi_ai_client`."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import pytest

from echo.tools.multi_ai_client import ApiCallResult, MultiAIClient, summarise_results


@dataclass
class _FakeResponse:
    status_code: int
    json_payload: Any
    text_payload: str

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 400

    def json(self) -> Any:
        if isinstance(self.json_payload, Exception):
            raise self.json_payload
        return self.json_payload

    @property
    def text(self) -> str:
        return self.text_payload


class _StubClient:
    def __init__(self, responses: Dict[str, _FakeResponse]) -> None:
        self.responses = responses
        self.calls: List[Dict[str, Any]] = []

    def post(self, url: str, *, json: Any, headers: Dict[str, str], auth, timeout) -> _FakeResponse:
        self.calls.append({
            "url": url,
            "json": json,
            "headers": headers,
            "auth": auth,
            "timeout": timeout,
        })
        if url not in self.responses:
            raise RuntimeError(f"Unexpected URL {url}")
        return self.responses[url]

    def close(self) -> None:
        pass


def test_invoke_success(tmp_path: Path) -> None:
    output_dir = tmp_path / "echo_output"
    response = _FakeResponse(200, {"message": "ok"}, "{\n  \"message\": \"ok\"\n}")
    client = _StubClient({"https://example.com/app": response})

    multi_client = MultiAIClient({"demo": "https://example.com/app"}, client=client, output_dir=output_dir)
    result = multi_client.invoke("demo", payload={"prompt": "hi"})

    assert result == ApiCallResult(
        app="demo",
        status_code=200,
        ok=True,
        payload={"message": "ok"},
        error=None,
        output_path=output_dir / "demo.json",
        response_text="{\n  \"message\": \"ok\"\n}",
    )
    assert result.output_path and result.output_path.read_text(encoding="utf-8") == "{\n  \"message\": \"ok\"\n}"
    assert client.calls[0]["json"] == {"prompt": "hi"}


def test_invoke_http_error_reports_body_excerpt(tmp_path: Path) -> None:
    output_dir = tmp_path / "echo_output"
    response = _FakeResponse(400, ValueError("boom"), "{\n  \"error\": \"missing prompt\"\n}\n")
    client = _StubClient({"https://example.com/app": response})
    multi_client = MultiAIClient({"demo": "https://example.com/app"}, client=client, output_dir=output_dir)

    result = multi_client.invoke("demo")

    assert not result.ok
    assert result.error == "HTTP 400: {\n  \"error\": \"missing prompt\"\n}"
    assert result.output_path is None


def test_invoke_parses_non_json_failure(tmp_path: Path) -> None:
    output_dir = tmp_path / "echo_output"
    response = _FakeResponse(500, ValueError("no json"), "Internal Server Error")
    client = _StubClient({"https://example.com/app": response})
    multi_client = MultiAIClient({"demo": "https://example.com/app"}, client=client, output_dir=output_dir)

    result = multi_client.invoke("demo")

    assert result.error == "HTTP 500: Internal Server Error"
    assert result.response_text == "Internal Server Error"


def test_invoke_all_applies_payload_defaults(tmp_path: Path) -> None:
    output_dir = tmp_path / "echo_output"
    responses = {
        "https://example.com/llama": _FakeResponse(200, {"id": 1}, "{\n  \"id\": 1\n}"),
        "https://example.com/gemini": _FakeResponse(200, {"id": 2}, "{\n  \"id\": 2\n}"),
    }
    client = _StubClient(responses)
    multi_client = MultiAIClient(
        {"llama": "https://example.com/llama", "gemini": "https://example.com/gemini"},
        client=client,
        output_dir=output_dir,
        auth=("user", "pass"),
    )

    results = multi_client.invoke_all(
        base_payload={"prompt": "hello"},
        per_app_payloads={"gemini": {"prompt": "gemini"}},
        timeout=3.0,
    )

    assert all(result.ok for result in results)
    llama_call, gemini_call = client.calls
    assert llama_call["json"] == {"prompt": "hello"}
    assert gemini_call["json"] == {"prompt": "gemini"}
    assert llama_call["auth"] == ("user", "pass")
    summary = summarise_results(results)
    assert "llama: ok" in summary
    assert "gemini: ok" in summary


def test_unknown_application_raises_keyerror(tmp_path: Path) -> None:
    multi_client = MultiAIClient({"llama": "https://example.com/llama"}, output_dir=tmp_path)
    with pytest.raises(KeyError):
        multi_client.invoke("doppler")


def test_empty_endpoint_map_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        MultiAIClient({}, output_dir=tmp_path)

