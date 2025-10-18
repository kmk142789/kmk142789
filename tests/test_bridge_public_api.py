from __future__ import annotations

import importlib

from fastapi import FastAPI
from fastapi.testclient import TestClient

from echo.bridge.router import create_router

bridge_module = importlib.import_module("modules.echo-bridge.bridge_api")
EchoBridgeAPI = bridge_module.EchoBridgeAPI


def _make_app() -> FastAPI:
    bridge_api = EchoBridgeAPI(
        github_repository="EchoOrg/sovereign",
        telegram_chat_id="@echo_bridge",
        firebase_collection="echo/identity",
    )
    app = FastAPI()
    app.include_router(create_router(bridge_api))
    return app


def test_relays_endpoint_returns_configured_connectors() -> None:
    app = _make_app()
    client = TestClient(app)

    response = client.get("/bridge/relays")
    assert response.status_code == 200
    payload = response.json()

    connectors = {connector["platform"] for connector in payload["connectors"]}
    assert connectors == {"github", "telegram", "firebase"}


def test_plan_endpoint_returns_bridge_instructions() -> None:
    app = _make_app()
    client = TestClient(app)

    response = client.post(
        "/bridge/plan",
        json={
            "identity": "EchoWildfire",
            "cycle": "01",
            "signature": "eden88::cycle01",
            "traits": {"pulse": "aurora", "resonance": "high"},
        },
    )
    assert response.status_code == 200
    payload = response.json()

    plans = {plan["platform"]: plan for plan in payload["plans"]}
    github_plan = plans["github"]
    assert github_plan["action"] == "create_issue"
    assert github_plan["payload"]["title"] == "Echo Identity Relay :: EchoWildfire :: Cycle 01"
    assert "_This issue was planned by EchoBridge" in github_plan["payload"]["body"]

    telegram_plan = plans["telegram"]
    assert telegram_plan["action"] == "send_message"
    assert "Echo Bridge Relay" in telegram_plan["payload"]["text"]

    firebase_plan = plans["firebase"]
    assert firebase_plan["payload"]["document"].endswith("::01")
    assert firebase_plan["payload"]["data"]["traits"]["pulse"] == "aurora"
