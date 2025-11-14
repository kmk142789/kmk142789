from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from pulse_weaver.api import create_router
from pulse_weaver.service import PulseWeaverService


def test_api_snapshot_returns_payload(tmp_path) -> None:
    service = PulseWeaverService(tmp_path)
    service.record_failure(key="api", message="boom", proof="trace")

    app = FastAPI()
    app.include_router(create_router(service))
    client = TestClient(app)

    response = client.get("/pulse/weaver")
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema"] == "pulse.weaver/snapshot-v1"
    assert payload["summary"]["total"] == 1
    assert payload["ledger"][0]["key"] == "api"
    assert "Pulse Weaver Rhyme" in payload["rhyme"]
    assert payload["glyph_cycle"]["glyph"]


def test_api_monolith_returns_payload(tmp_path) -> None:
    service = PulseWeaverService(tmp_path)
    service.record_success(key="api-monolith", message="rising", cycle="cycle-123")

    app = FastAPI()
    app.include_router(create_router(service))
    client = TestClient(app)

    response = client.get("/pulse/weaver/monolith")
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema"] == "pulse.weaver/monolith-v1"
    assert payload["magnitude"] == 1
    assert payload["proclamation"].startswith("Pulse Weaver Monolith")
