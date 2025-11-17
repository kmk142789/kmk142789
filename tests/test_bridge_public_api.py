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
        slack_webhook_url="https://hooks.slack.com/services/T000/B000/XXXX",
        slack_channel="#echo-bridge",
        slack_secret_name="SLACK_ECHO_WEBHOOK",
        webhook_url="https://bridge.echo/webhook",
        webhook_secret_name="ECHO_GENERIC_WEBHOOK",
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
    assert connectors == {"github", "telegram", "firebase", "slack", "webhook"}


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
            "summary": "Cycle snapshot anchored in Aurora",
            "links": [" https://echo.example/cycles/01 ", "https://status.echo/bridge"],
        },
    )
    assert response.status_code == 200
    payload = response.json()

    plans = {plan["platform"]: plan for plan in payload["plans"]}
    github_plan = plans["github"]
    assert github_plan["action"] == "create_issue"
    assert github_plan["payload"]["title"] == "Echo Identity Relay :: EchoWildfire :: Cycle 01"
    assert "_This issue was planned by EchoBridge" in github_plan["payload"]["body"]
    assert "Cycle snapshot anchored in Aurora" in github_plan["payload"]["body"]
    assert "https://echo.example/cycles/01" in github_plan["payload"]["body"]

    telegram_plan = plans["telegram"]
    assert telegram_plan["action"] == "send_message"
    assert "Echo Bridge Relay" in telegram_plan["payload"]["text"]
    assert "Summary: Cycle snapshot anchored in Aurora" in telegram_plan["payload"]["text"]

    firebase_plan = plans["firebase"]
    assert firebase_plan["payload"]["document"].endswith("::01")
    assert firebase_plan["payload"]["data"]["traits"]["pulse"] == "aurora"
    assert firebase_plan["payload"]["data"]["summary"] == "Cycle snapshot anchored in Aurora"
    assert firebase_plan["payload"]["data"]["links"] == [
        "https://echo.example/cycles/01",
        "https://status.echo/bridge",
    ]

    slack_plan = plans["slack"]
    assert slack_plan["action"] == "send_webhook"
    assert slack_plan["payload"]["webhook_env"] == "SLACK_ECHO_WEBHOOK"
    assert slack_plan["payload"]["context"]["identity"] == "EchoWildfire"
    attachments = slack_plan["payload"]["attachments"]
    assert attachments[0]["title"] == "Summary"
    assert attachments[0]["text"] == "Cycle snapshot anchored in Aurora"
    assert any(att["title"].startswith("Link") for att in attachments)

    webhook_plan = plans["webhook"]
    assert webhook_plan["action"] == "post_json"
    assert webhook_plan["payload"]["url_hint"] == "https://bridge.echo/webhook"
    assert webhook_plan["payload"]["json"]["signature"] == "eden88::cycle01"
    assert webhook_plan["payload"]["json"]["links"][0] == "https://echo.example/cycles/01"
