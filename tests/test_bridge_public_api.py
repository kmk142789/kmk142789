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
        discord_webhook_url="https://discord.com/api/webhooks/ABC",
        discord_secret_name="DISCORD_ECHO_WEBHOOK",
        bluesky_identifier="echo.bridge",
        bluesky_service_url="https://bsky.social",
        bluesky_app_password_secret="ECHO_BLUESKY_SECRET",
        mastodon_instance_url="https://echo.social",
        mastodon_visibility="direct",
        mastodon_secret_name="ECHO_MASTODON_TOKEN",
        matrix_homeserver="https://matrix.echo",
        matrix_room_id="!echo:matrix",
        matrix_secret_name="ECHO_MATRIX_TOKEN",
        activitypub_inbox_url="https://echo.social/inbox",
        activitypub_actor="https://echo.social/@bridge",
        activitypub_secret_name="ECHO_ACTIVITYPUB_SECRET",
        teams_webhook_url="https://teams.echo/hooks/123",
        teams_secret_name="ECHO_TEAMS_WEBHOOK",
        farcaster_identity="echo.bridge",
        farcaster_secret_name="ECHO_FARCASTER_SIGNING_KEY",
        nostr_relays=["wss://relay.echo", "wss://relay.backup"],
        nostr_public_key="npub1echo123",
        nostr_secret_name="ECHO_NOSTR_PRIVATE_KEY",
        sms_recipients=["+15551234567", "+15559876543"],
        sms_secret_name="ECHO_TWILIO_TOKEN",
        sms_from_number="+15550001111",
        statuspage_page_id="echo-status",
        statuspage_secret_name="ECHO_STATUSPAGE_TOKEN",
        email_recipients=["ops@echo.test", "alerts@echo.test"],
        email_secret_name="SENDGRID_TOKEN",
        email_subject_template="Echo Relay {identity}/{cycle}",
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
    assert connectors == {
        "github",
        "telegram",
        "firebase",
        "slack",
        "webhook",
        "discord",
        "bluesky",
        "email",
        "mastodon",
        "matrix",
        "activitypub",
        "teams",
        "farcaster",
        "nostr",
        "sms",
        "statuspage",
    }


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
            "topics": ["Pulse Orbit", "Echo Bridge", "echo bridge"],
            "priority": "high",
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
    assert "Priority: high" in telegram_plan["payload"]["text"]
    assert "Topics:" in telegram_plan["payload"]["text"]

    firebase_plan = plans["firebase"]
    assert firebase_plan["payload"]["document"].endswith("::01")
    assert firebase_plan["payload"]["data"]["traits"]["pulse"] == "aurora"
    assert firebase_plan["payload"]["data"]["summary"] == "Cycle snapshot anchored in Aurora"
    assert firebase_plan["payload"]["data"]["links"] == [
        "https://echo.example/cycles/01",
        "https://status.echo/bridge",
    ]
    assert firebase_plan["payload"]["data"]["priority"] == "high"
    assert firebase_plan["payload"]["data"]["topics"] == [
        "Pulse Orbit",
        "Echo Bridge",
    ]

    slack_plan = plans["slack"]
    assert slack_plan["action"] == "send_webhook"
    assert slack_plan["payload"]["webhook_env"] == "SLACK_ECHO_WEBHOOK"
    assert slack_plan["payload"]["context"]["identity"] == "EchoWildfire"
    attachments = {att["title"]: att["text"] for att in slack_plan["payload"].get("attachments", [])}
    assert attachments["Summary"] == "Cycle snapshot anchored in Aurora"
    assert attachments["Priority"] == "high"
    assert attachments["Topics"] == "Pulse Orbit, Echo Bridge"
    assert any(title.startswith("Link") for title in attachments)

    webhook_plan = plans["webhook"]
    assert webhook_plan["action"] == "post_json"
    assert webhook_plan["payload"]["url_hint"] == "https://bridge.echo/webhook"
    assert webhook_plan["payload"]["json"]["signature"] == "eden88::cycle01"
    assert webhook_plan["payload"]["json"]["links"][0] == "https://echo.example/cycles/01"

    discord_plan = plans["discord"]
    assert discord_plan["action"] == "send_webhook"
    assert discord_plan["payload"]["webhook_env"] == "DISCORD_ECHO_WEBHOOK"
    assert discord_plan["payload"]["context"]["cycle"] == "01"
    assert discord_plan["payload"].get("embeds")
    embed_fields = {field["name"]: field["value"] for field in discord_plan["payload"]["embeds"][0]["fields"]}
    assert embed_fields["Priority"] == "high"
    assert embed_fields["Topics"] == "Pulse Orbit, Echo Bridge"

    email_plan = plans["email"]
    assert email_plan["action"] == "send_email"
    assert email_plan["payload"]["recipients"] == ["ops@echo.test", "alerts@echo.test"]
    assert email_plan["payload"]["subject"] == "Echo Relay EchoWildfire/01"
    assert "Echo Bridge Relay" in email_plan["payload"]["body"]
    assert email_plan["payload"]["priority"] == "high"
    assert email_plan["payload"]["topics"] == ["Pulse Orbit", "Echo Bridge"]

    bluesky_plan = plans["bluesky"]
    assert bluesky_plan["action"] == "post_record"
    assert bluesky_plan["payload"]["identifier"] == "echo.bridge"
    assert "#EchoBridge" in bluesky_plan["payload"]["text"]
    assert bluesky_plan["payload"].get("tags")

    mastodon_plan = plans["mastodon"]
    assert mastodon_plan["action"] == "post_status"
    assert mastodon_plan["payload"]["instance"] == "https://echo.social"
    assert mastodon_plan["payload"]["visibility"] == "direct"
    assert "#EchoBridge" in mastodon_plan["payload"]["status"]
    assert mastodon_plan["payload"]["context"]["identity"] == "EchoWildfire"
    assert mastodon_plan["payload"]["tags"] == ["Pulse Orbit", "Echo Bridge"]
    assert mastodon_plan["payload"]["priority"] == "high"

    matrix_plan = plans["matrix"]
    assert matrix_plan["action"] == "send_room_message"
    assert matrix_plan["payload"]["homeserver"] == "https://matrix.echo"
    assert matrix_plan["payload"]["room_id"] == "!echo:matrix"
    assert "Cycle 01" in matrix_plan["payload"]["text"]
    assert matrix_plan["payload"]["topics"] == ["Pulse Orbit", "Echo Bridge"]
    assert matrix_plan["payload"]["priority"] == "high"

    activitypub_plan = plans["activitypub"]
    assert activitypub_plan["action"] == "deliver_note"
    assert activitypub_plan["payload"]["inbox"] == "https://echo.social/inbox"
    assert activitypub_plan["payload"]["actor"] == "https://echo.social/@bridge"
    assert activitypub_plan["payload"]["context"]["identity"] == "EchoWildfire"

    teams_plan = plans["teams"]
    assert teams_plan["action"] == "send_webhook"
    assert teams_plan["payload"]["webhook_env"] == "ECHO_TEAMS_WEBHOOK"
    assert teams_plan["payload"]["context"]["cycle"] == "01"
    assert teams_plan["payload"]["priority"] == "high"
    assert teams_plan["payload"]["topics"] == ["Pulse Orbit", "Echo Bridge"]

    farcaster_plan = plans["farcaster"]
    assert farcaster_plan["action"] == "post_cast"
    assert farcaster_plan["payload"]["identity"] == "echo.bridge"
    assert "#EchoBridge" in farcaster_plan["payload"]["text"]
    assert farcaster_plan["payload"]["attachments"][0] == "https://echo.example/cycles/01"

    sms_plan = plans["sms"]
    assert sms_plan["action"] == "send_sms"
    assert sms_plan["payload"]["recipients"] == ["+15551234567", "+15559876543"]
    assert sms_plan["payload"]["from_number"] == "+15550001111"
    assert "Echo Bridge Relay" in sms_plan["payload"]["body"]
    assert sms_plan["payload"]["priority"] == "high"
    assert sms_plan["requires_secret"] == ["ECHO_TWILIO_TOKEN"]

    statuspage_plan = plans["statuspage"]
    assert statuspage_plan["action"] == "create_incident"
    assert statuspage_plan["payload"]["page_id"] == "echo-status"
    incident = statuspage_plan["payload"]["incident"]
    assert incident["impact_override"] == "major"
    assert incident["status"] == "investigating"
    assert incident["metadata"]["topics"] == ["Pulse Orbit", "Echo Bridge"]
    assert incident["summary"] == "Cycle snapshot anchored in Aurora"

    nostr_plan = plans["nostr"]
    assert nostr_plan["action"] == "post_event"
    assert nostr_plan["payload"]["relays"] == ["wss://relay.echo", "wss://relay.backup"]
    assert nostr_plan["payload"]["pubkey"] == "npub1echo123"
    assert "#EchoBridge" in nostr_plan["payload"]["content"]
    assert ["t", "PulseOrbit"] in nostr_plan["payload"]["tags"]
    assert nostr_plan["requires_secret"] == ["ECHO_NOSTR_PRIVATE_KEY"]


def test_plan_endpoint_filters_requested_connectors() -> None:
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
            "topics": ["Pulse Orbit", "Echo Bridge", "echo bridge"],
            "priority": "high",
            "connectors": ["slack", "webhook"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    platforms = {plan["platform"] for plan in payload["plans"]}
    assert platforms == {"slack", "webhook"}
    for plan in payload["plans"]:
        if plan["platform"] == "slack":
            assert plan["payload"]["webhook_env"] == "SLACK_ECHO_WEBHOOK"
        if plan["platform"] == "webhook":
            assert plan["payload"]["url_hint"] == "https://bridge.echo/webhook"
