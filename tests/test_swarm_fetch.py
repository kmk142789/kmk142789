from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from tools import swarm_fetch


def test_parse_swarm_uri_handles_common_forms():
    uri = swarm_fetch.parse_swarm_uri("bzzr://deadbeef/path/to/resource")
    assert uri.scheme == "bzzr"
    assert uri.reference == "deadbeef"
    assert uri.path == "path/to/resource"

    uri = swarm_fetch.parse_swarm_uri("bzzr:deadbeef")
    assert uri.scheme == "bzzr"
    assert uri.reference == "deadbeef"
    assert uri.path == ""


def test_parse_swarm_uri_rejects_invalid_scheme():
    with pytest.raises(ValueError):
        swarm_fetch.parse_swarm_uri("ipfs://hash")


def test_resolve_swarm_uri_uses_gateway_and_normalises_scheme(monkeypatch):
    monkeypatch.setenv("SWARM_HTTP_GATEWAY", "https://example.invalid")
    url = swarm_fetch.resolve_swarm_uri("bzzr://cafebabe")
    assert url == "https://example.invalid/bzz-raw:/cafebabe/"

    url = swarm_fetch.resolve_swarm_uri(
        "bzz://cafebabe/manifest.json", gateway="https://gateway.test"
    )
    assert url == "https://gateway.test/bzz:/cafebabe/manifest.json"


def test_fetch_swarm_uri_uses_injected_opener():
    expected_url = "https://swarm-gateways.net/bzz-raw:/abc123/"
    captured: dict[str, str] = {}

    class DummyResponse:
        def __init__(self, data: bytes) -> None:
            self._data = data

        def __enter__(self) -> "DummyResponse":
            return self

        def __exit__(self, *exc: object) -> None:
            return None

        def read(self) -> bytes:
            return self._data

    def opener(url: str) -> DummyResponse:
        captured["url"] = url
        return DummyResponse(b"payload")

    data = swarm_fetch.fetch_swarm_uri("bzzr://abc123", opener=opener)
    assert captured["url"] == expected_url
    assert data == b"payload"


def test_main_writes_payload_to_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    output = tmp_path / "artifact.bin"
    calls = {}

    def fake_resolve(uri: str, *, gateway: str | None = None) -> str:  # noqa: ANN001
        calls["resolve"] = SimpleNamespace(uri=uri, gateway=gateway)
        return "https://gateway.test/bzz-raw:/abc123/"

    def fake_fetch(uri: str, *, gateway: str | None = None, opener=None) -> bytes:  # noqa: ANN001
        calls["fetch"] = SimpleNamespace(uri=uri, gateway=gateway, opener=opener)
        return b"payload"

    monkeypatch.setattr(swarm_fetch, "resolve_swarm_uri", fake_resolve)
    monkeypatch.setattr(swarm_fetch, "fetch_swarm_uri", fake_fetch)

    exit_code = swarm_fetch.main(["bzzr://abc123", "--output", str(output), "--gateway", "https://custom"])
    assert exit_code == 0
    assert output.read_bytes() == b"payload"
    assert calls["resolve"].gateway == "https://custom"
    assert calls["fetch"].gateway == "https://custom"


def test_main_dry_run_skips_download(monkeypatch: pytest.MonkeyPatch):
    called = {}

    def fake_resolve(uri: str, *, gateway: str | None = None) -> str:  # noqa: ANN001
        called["resolve"] = True
        return "https://gateway/bzz-raw:/abc123/"

    def fake_fetch(*args, **kwargs):  # noqa: ANN001, D401
        raise AssertionError("fetch should not be invoked in dry-run mode")

    monkeypatch.setattr(swarm_fetch, "resolve_swarm_uri", fake_resolve)
    monkeypatch.setattr(swarm_fetch, "fetch_swarm_uri", fake_fetch)

    exit_code = swarm_fetch.main(["bzzr://abc123", "--dry-run"])
    assert exit_code == 0
    assert called["resolve"] is True
