from __future__ import annotations

import importlib

from fastapi import FastAPI
from fastapi.testclient import TestClient
import hashlib

from echo.bridge import BridgeSyncService
from echo.bridge.router import create_router
from echo.bridge.secrets import BridgeSecretStore

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
        notion_database_id="bridge-db-01",
        notion_secret_name="ECHO_NOTION_TOKEN",
        dns_root_domain="echo.test",
        dns_record_prefix="_echo",
        dns_provider="root-authority",
        dns_secret_name="ECHO_DNS_TOKEN",
        dns_root_authority="echo.root",
        dns_attestation_path="attestations/dns/echo.root.zone",
        linkedin_organization_id="echo-org-01",
        linkedin_secret_name="ECHO_LINKEDIN_TOKEN",
        reddit_subreddit="echo_bridge",
        reddit_secret_name="ECHO_REDDIT_TOKEN",
        pagerduty_routing_key_secret="ECHO_PAGERDUTY_ROUTING_KEY",
        pagerduty_source="echo-bridge-api",
        pagerduty_component="relay",
        pagerduty_group="echo-ops",
        opsgenie_api_key_secret="ECHO_OPSGENIE_TOKEN",
        opsgenie_team="echo-ops-team",
        arweave_gateway_url="https://arweave.net",
        arweave_wallet_secret_name="ECHO_ARWEAVE_JWK",
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
        "notion",
        "dns",
        "linkedin",
        "reddit",
        "pagerduty",
        "opsgenie",
        "arweave",
    }


def test_relays_endpoint_optionally_includes_sync_connectors() -> None:
    app = _make_app()
    client = TestClient(app)

    response = client.get("/bridge/relays", params={"include_sync": True})
    assert response.status_code == 200
    payload = response.json()

    sync_connectors = payload.get("sync_connectors")
    assert sync_connectors is not None
    platforms = {connector["platform"] for connector in sync_connectors}
    assert platforms >= {"domains", "unstoppable", "vercel", "github"}
    github = next(item for item in sync_connectors if item["platform"] == "github")
    assert github["requires_secrets"] == ["GITHUB_TOKEN"]


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


def test_plan_endpoint_stores_secret_payload_privately(tmp_path) -> None:
    app = FastAPI()
    bridge_api = EchoBridgeAPI(
        github_repository="EchoOrg/sovereign",
        firebase_collection="echo/identity",
    )
    secret_store = BridgeSecretStore(tmp_path)
    app.include_router(create_router(bridge_api, secret_store=secret_store))
    client = TestClient(app)

    secret = b"secret-echo"
    encoded = "c2VjcmV0LWVjaG8="
    expected_hash = hashlib.sha256(secret).hexdigest()

    response = client.post(
        "/bridge/plan",
        json={
            "identity": "EchoWildfire",
            "cycle": "02",
            "signature": "eden88::cycle02",
            "secret_payload": encoded,
            "secret_label": "vault-fragment",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    plans = {plan["platform"]: plan for plan in payload["plans"]}
    firebase_plan = plans["firebase"]
    decoded = firebase_plan["payload"]["data"]["decoded_payload"]
    assert decoded["sha256"] == expected_hash
    assert decoded["bytes"] == len(secret)
    assert decoded["label"] == "vault-fragment"
    assert decoded["encoding"] == "base64"
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

    notion_plan = plans["notion"]
    assert notion_plan["action"] == "create_page"
    notion_props = notion_plan["payload"]["properties"]
    assert notion_props["Priority"]["select"]["name"] == "high"
    assert [entry["name"] for entry in notion_props["Topics"]["multi_select"]] == [
        "Pulse Orbit",
        "Echo Bridge",
    ]
    assert notion_plan["payload"]["context"]["identity"] == "EchoWildfire"
    children = notion_plan["payload"]["children"]
    assert any(block.get("type") == "paragraph" for block in children)

    dns_plan = plans["dns"]
    assert dns_plan["action"] == "upsert_txt_record"
    assert dns_plan["payload"]["root_domain"] == "echo.test"
    assert dns_plan["payload"]["record"] == "_echo.echo.test"
    assert (
        dns_plan["payload"]["value"]
        == "echo-root=EchoWildfire:01:eden88::cycle01"
    )
    assert dns_plan["payload"]["authority"]["root"] == "echo.root"
    assert dns_plan["payload"]["authority"]["provider"] == "root-authority"
    assert dns_plan["payload"]["authority"]["record_prefix"] == "_echo"
    assert dns_plan["payload"]["authority"]["attestation"] == "attestations/dns/echo.root.zone"
    assert dns_plan["payload"]["context"]["topics"] == ["Pulse Orbit", "Echo Bridge"]
    assert dns_plan["requires_secret"] == ["ECHO_DNS_TOKEN"]

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

    pagerduty_plan = plans["pagerduty"]
    assert pagerduty_plan["action"] == "trigger_event"
    assert pagerduty_plan["payload"]["routing_key_env"] == "ECHO_PAGERDUTY_ROUTING_KEY"
    assert pagerduty_plan["payload"]["payload"]["severity"] == "error"
    assert pagerduty_plan["payload"]["payload"]["source"] == "echo-bridge-api"
    assert pagerduty_plan["payload"]["payload"]["component"] == "relay"
    assert pagerduty_plan["payload"]["payload"]["group"] == "echo-ops"
    assert pagerduty_plan["requires_secret"] == ["ECHO_PAGERDUTY_ROUTING_KEY"]

    opsgenie_plan = plans["opsgenie"]
    assert opsgenie_plan["action"] == "create_alert"
    assert opsgenie_plan["payload"]["api_key_env"] == "ECHO_OPSGENIE_TOKEN"
    assert opsgenie_plan["payload"]["priority"] == "P2"
    assert opsgenie_plan["payload"]["responders"][0]["name"] == "echo-ops-team"
    assert "EchoBridge" in opsgenie_plan["payload"]["tags"]
    assert opsgenie_plan["requires_secret"] == ["ECHO_OPSGENIE_TOKEN"]

    arweave_plan = plans["arweave"]
    assert arweave_plan["action"] == "submit_transaction"
    assert arweave_plan["payload"]["gateway_url"] == "https://arweave.net"
    assert arweave_plan["payload"]["transaction"]["content_type"] == "application/json"
    assert {tag["name"] for tag in arweave_plan["payload"]["transaction"]["tags"]} >= {
        "App-Name",
        "Identity",
        "Cycle",
    }
    assert arweave_plan["payload"]["transaction"]["data"]["identity"] == "EchoWildfire"
    assert arweave_plan["requires_secret"] == ["ECHO_ARWEAVE_JWK"]

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


def test_dns_plan_supports_additional_domains() -> None:
    api = EchoBridgeAPI(
        dns_root_domain="echo.test",
        dns_additional_root_domains=[" echo.alt ", "echo.test", "bridge.echo"],
        dns_record_prefix="_echo",
        dns_provider="root-authority",
        dns_secret_name="ECHO_DNS_TOKEN",
        dns_root_authority="echo.root",
        dns_attestation_path="attestations/dns/echo.root.zone",
    )
    app = FastAPI()
    app.include_router(create_router(api=api))
    client = TestClient(app)

    relays = client.get("/bridge/relays")
    assert relays.status_code == 200
    connectors = {connector["platform"]: connector for connector in relays.json()["connectors"]}
    assert set(connectors) == {"dns"}
    assert connectors["dns"]["requires_secrets"] == ["ECHO_DNS_TOKEN"]

    response = client.post(
        "/bridge/plan",
        json={
            "identity": "EchoWildfire",
            "cycle": "21",
            "signature": "eden88::cycle21",
            "traits": {"pulse": "aurora"},
            "summary": "Bridge all domains",
            "links": ["https://echo.example/cycles/21"],
            "topics": ["Echo Bridge"],
            "priority": "high",
        },
    )

    assert response.status_code == 200
    plans = {plan["platform"]: plan for plan in response.json()["plans"]}
    dns_plan = plans["dns"]
    payload = dns_plan["payload"]

    assert payload["root_domain"] == "echo.test"
    assert payload["record"] == "_echo.echo.test"
    assert payload["value"] == "echo-root=EchoWildfire:21:eden88::cycle21"
    assert payload["authority"]["attestation"] == "attestations/dns/echo.root.zone"

    records = payload["records"]
    assert {record["root_domain"] for record in records} == {
        "echo.test",
        "echo.alt",
        "bridge.echo",
    }
    assert all(record["record"].startswith("_echo.") for record in records)
    assert all(record["value"] == payload["value"] for record in records)


def test_plan_supports_linkedin_and_reddit_connectors() -> None:
    api = EchoBridgeAPI(
        linkedin_organization_id="echo-org-01",
        linkedin_secret_name="ECHO_LINKEDIN_TOKEN",
        reddit_subreddit="echo_bridge",
        reddit_secret_name="ECHO_REDDIT_TOKEN",
        pagerduty_routing_key_secret="ECHO_PAGERDUTY_ROUTING_KEY",
        pagerduty_source="echo-bridge-api",
        pagerduty_component="relay",
        pagerduty_group="echo-ops",
        opsgenie_api_key_secret="ECHO_OPSGENIE_TOKEN",
        opsgenie_team="echo-ops-team",
    )
    app = FastAPI()
    app.include_router(create_router(api=api))
    client = TestClient(app)

    relays = client.get("/bridge/relays")
    assert relays.status_code == 200
    connectors = {connector["platform"] for connector in relays.json()["connectors"]}
    assert connectors == {"linkedin", "reddit", "pagerduty", "opsgenie"}

    response = client.post(
        "/bridge/plan",
        json={
            "identity": "EchoWildfire",
            "cycle": "07",
            "signature": "eden88::cycle07",
            "traits": {"pulse": "aurora"},
            "summary": "Cycle 07 resonance",
            "links": ["https://echo.example/cycles/07"],
            "topics": ["Echo Bridge", "pulse orbit"],
            "priority": "critical",
        },
    )

    assert response.status_code == 200
    plans = {plan["platform"]: plan for plan in response.json()["plans"]}

    linkedin = plans["linkedin"]
    assert linkedin["action"] == "create_share"
    assert linkedin["payload"]["organization_id"] == "echo-org-01"
    assert linkedin["payload"]["context"]["identity"] == "EchoWildfire"
    assert linkedin["payload"]["priority"] == "critical"
    assert "EchoBridge" in linkedin["payload"]["tags"]
    assert linkedin["requires_secret"] == ["ECHO_LINKEDIN_TOKEN"]

    reddit = plans["reddit"]
    assert reddit["action"] == "submit_post"
    assert reddit["payload"]["subreddit"] == "echo_bridge"
    assert reddit["payload"]["title"] == "Echo Relay EchoWildfire/07"
    assert reddit["payload"]["priority"] == "critical"
    assert "pulse orbit" in reddit["payload"]["topics"]
    assert reddit["payload"]["links"] == ["https://echo.example/cycles/07"]
    assert reddit["requires_secret"] == ["ECHO_REDDIT_TOKEN"]

    pagerduty = plans["pagerduty"]
    assert pagerduty["action"] == "trigger_event"
    assert pagerduty["payload"]["routing_key_env"] == "ECHO_PAGERDUTY_ROUTING_KEY"
    assert pagerduty["payload"]["payload"]["severity"] == "critical"

    opsgenie = plans["opsgenie"]
    assert opsgenie["action"] == "create_alert"
    assert opsgenie["payload"]["priority"] == "P1"
    assert "EchoBridge" in opsgenie["payload"]["tags"]


def test_plan_supports_unstoppable_and_vercel_connectors() -> None:
    api = EchoBridgeAPI(
        unstoppable_domains=["echo.crypto", " echo.crypto ", "nexus.crypto"],
        unstoppable_secret_name="ECHO_UNSTOPPABLE_SECRET",
        vercel_projects=["dashboard", "console"],
        vercel_secret_name="ECHO_VERCEL_TOKEN",
    )
    app = FastAPI()
    app.include_router(create_router(api=api))
    client = TestClient(app)

    relays = client.get("/bridge/relays")
    assert relays.status_code == 200
    connectors = {connector["platform"] for connector in relays.json()["connectors"]}
    assert connectors == {"unstoppable", "vercel"}

    response = client.post(
        "/bridge/plan",
        json={
            "identity": "EchoWildfire",
            "cycle": "09",
            "signature": "eden88::cycle09",
            "traits": {"pulse": "aurora"},
            "summary": "Advance bridge payload",
            "links": ["https://echo.example/cycles/09"],
            "topics": ["Bridge Upgrades", "bridge upgrades"],
            "priority": "critical",
        },
    )

    assert response.status_code == 200
    plans = {plan["platform"]: plan for plan in response.json()["plans"]}

    unstoppable = plans["unstoppable"]
    assert unstoppable["action"] == "update_domain_records"
    assert unstoppable["payload"]["domains"] == ["echo.crypto", "nexus.crypto"]
    records = unstoppable["payload"]["records"]
    assert records["echo.identity"] == "EchoWildfire"
    assert records["echo.cycle"] == "09"
    assert records["echo.summary"] == "Advance bridge payload"
    assert records["echo.links"] == ["https://echo.example/cycles/09"]
    assert records["echo.topics"] == ["Bridge Upgrades"]
    assert records["echo.priority"] == "critical"
    assert records["echo.traits"]["pulse"] == "aurora"
    assert unstoppable["requires_secret"] == ["ECHO_UNSTOPPABLE_SECRET"]

    vercel = plans["vercel"]
    assert vercel["action"] == "trigger_deploy"
    assert vercel["payload"]["projects"] == ["dashboard", "console"]
    context = vercel["payload"]["context"]
    assert context["identity"] == "EchoWildfire"
    assert context["cycle"] == "09"
    assert context["summary"] == "Advance bridge payload"
    assert context["links"] == ["https://echo.example/cycles/09"]
    assert context["topics"] == ["Bridge Upgrades"]
    assert context["priority"] == "critical"
    assert vercel["requires_secret"] == ["ECHO_VERCEL_TOKEN"]


def test_plan_supports_kafka_and_s3_connectors() -> None:
    api = EchoBridgeAPI(
        kafka_topic="echo.bridge",
        kafka_bootstrap_servers=[" kafka:9092", "kafka:9092", "backup:9093"],
        kafka_secret_name="ECHO_KAFKA_SECRET",
        s3_bucket="echo-bridge-bucket",
        s3_prefix="relays/state",
        s3_region="us-east-2",
        s3_secret_name="ECHO_S3_SECRET",
    )
    app = FastAPI()
    app.include_router(create_router(api=api))
    client = TestClient(app)

    relays = client.get("/bridge/relays")
    assert relays.status_code == 200
    connectors = {connector["platform"]: connector for connector in relays.json()["connectors"]}
    assert {"kafka", "s3"} <= set(connectors)
    assert connectors["kafka"]["requires_secrets"] == ["ECHO_KAFKA_SECRET"]
    assert connectors["s3"]["requires_secrets"] == ["ECHO_S3_SECRET"]

    response = client.post(
        "/bridge/plan",
        json={
            "identity": "EchoWildfire",
            "cycle": "17",
            "signature": "eden88::cycle17",
            "traits": {"pulse": "aurora"},
            "summary": "New edge sync",
            "links": [" https://echo.example/cycles/17 ", "https://status.echo/bridge"],
            "topics": ["Bridge Orbit", "bridge orbit"],
            "priority": "high",
        },
    )

    assert response.status_code == 200
    plans = {plan["platform"]: plan for plan in response.json()["plans"]}

    kafka_plan = plans["kafka"]
    assert kafka_plan["action"] == "publish_event"
    assert kafka_plan["payload"]["topic"] == "echo.bridge"
    assert kafka_plan["payload"]["bootstrap_servers"] == ["kafka:9092", "backup:9093"]
    assert kafka_plan["payload"]["message"]["identity"] == "EchoWildfire"
    assert kafka_plan["payload"]["message"]["topics"] == ["Bridge Orbit"]
    context = kafka_plan["payload"]["context"]
    assert context["signature"] == "eden88::cycle17"
    assert context["summary"] == "New edge sync"
    assert context["links"] == ["https://echo.example/cycles/17", "https://status.echo/bridge"]
    assert context["traits"]["pulse"] == "aurora"
    assert kafka_plan["requires_secret"] == ["ECHO_KAFKA_SECRET"]

    s3_plan = plans["s3"]
    assert s3_plan["action"] == "write_object"
    assert s3_plan["payload"]["bucket"] == "echo-bridge-bucket"
    assert s3_plan["payload"]["region"] == "us-east-2"
    assert s3_plan["payload"]["key"] == "relays/state/echowildfire-17.json"
    assert s3_plan["payload"]["body"]["signature"] == "eden88::cycle17"
    assert s3_plan["payload"]["metadata"]["priority"] == "high"
    assert s3_plan["payload"]["metadata"]["signature"] == "eden88::cycle17"
    assert s3_plan["requires_secret"] == ["ECHO_S3_SECRET"]


def test_radio_plans_include_frequency_and_bandwidth() -> None:
    api = EchoBridgeAPI(
        wifi_ssid="EchoMesh",
        wifi_channel="6",
        wifi_bandwidth_mhz=40.0,
        bluetooth_beacon_id="echo-ble-01",
        bluetooth_profile="Mesh",
        bluetooth_bandwidth_mhz=2.0,
        bluetooth_frequency_mhz=2426.0,
    )
    app = FastAPI()
    app.include_router(create_router(api=api))
    client = TestClient(app)

    response = client.post(
        "/bridge/plan",
        json={
            "identity": "EchoWildfire",
            "cycle": "11",
            "signature": "eden88::cycle11",
            "traits": {"pulse": "aurora"},
            "summary": "Radio mesh upgrade",
            "links": ["https://echo.example/cycles/11"],
            "topics": ["Bridge Upgrades", "bandwidth"],
            "priority": "high",
        },
    )

    assert response.status_code == 200
    plans = {plan["platform"]: plan for plan in response.json()["plans"]}

    wifi_transport = plans["wifi"]["payload"]["transport"]
    assert wifi_transport["bandwidth_mhz"] == 40.0
    assert wifi_transport["frequency_mhz"] == 2437.0

    bluetooth_transport = plans["bluetooth"]["payload"]["transport"]
    assert bluetooth_transport["bandwidth_mhz"] == 2.0
    assert bluetooth_transport["frequency_mhz"] == 2426.0


def test_plan_supports_tcp_and_iot_connectors() -> None:
    api = EchoBridgeAPI(
        tcp_endpoints=[" localhost:9000", "echo.net:9001", "localhost:9000"],
        tcp_secret_name="ECHO_TCP_TOKEN",
        iot_channel="echo/bus",
        iot_secret_name="ECHO_IOT_TOKEN",
    )
    app = FastAPI()
    app.include_router(create_router(api=api))
    client = TestClient(app)

    relays = client.get("/bridge/relays")
    assert relays.status_code == 200
    connectors = {connector["platform"]: connector for connector in relays.json()["connectors"]}
    assert set(connectors) == {"tcp", "iot"}
    assert connectors["tcp"]["requires_secrets"] == ["ECHO_TCP_TOKEN"]
    assert connectors["iot"]["requires_secrets"] == ["ECHO_IOT_TOKEN"]

    response = client.post(
        "/bridge/plan",
        json={
            "identity": "EchoWildfire",
            "cycle": "13",
            "signature": "eden88::cycle13",
            "traits": {"pulse": "aurora"},
            "summary": "Bridge edge propagation",
            "links": [" https://echo.example/cycles/13 "],
            "topics": ["Edge", "bridge", "Edge"],
            "priority": "medium",
        },
    )

    assert response.status_code == 200
    plans = {plan["platform"]: plan for plan in response.json()["plans"]}

    tcp_plan = plans["tcp"]
    assert tcp_plan["action"] == "send_payload"
    assert tcp_plan["payload"]["endpoints"] == ["localhost:9000", "echo.net:9001"]
    assert "Echo Bridge Relay" in tcp_plan["payload"]["body"]
    assert tcp_plan["requires_secret"] == ["ECHO_TCP_TOKEN"]

    iot_plan = plans["iot"]
    assert iot_plan["action"] == "publish"
    assert iot_plan["payload"]["channel"] == "echo/bus"
    assert iot_plan["payload"]["payload"]["identity"] == "EchoWildfire"
    assert iot_plan["payload"]["payload"]["priority"] == "medium"
    assert iot_plan["payload"]["payload"]["links"] == ["https://echo.example/cycles/13"]
    assert iot_plan["payload"]["context"]["topics"] == ["Edge", "bridge"]
    assert iot_plan["requires_secret"] == ["ECHO_IOT_TOKEN"]


def test_plan_supports_github_discussions_and_rss_connectors() -> None:
    api = EchoBridgeAPI(
        github_discussions_repository="EchoOrg/sovereign",
        github_discussion_category="Bridge Updates",
        github_discussions_secret_name="ECHO_DISCUSS_TOKEN",
        rss_feed_url="https://echo.example/feed.xml",
        rss_secret_name="ECHO_RSS_TOKEN",
    )
    app = FastAPI()
    app.include_router(create_router(api=api))
    client = TestClient(app)

    relays = client.get("/bridge/relays")
    assert relays.status_code == 200
    connectors = {connector["platform"]: connector for connector in relays.json()["connectors"]}
    assert set(connectors) == {"github_discussions", "rss"}
    assert connectors["github_discussions"]["requires_secrets"] == ["ECHO_DISCUSS_TOKEN"]
    assert connectors["rss"]["requires_secrets"] == ["ECHO_RSS_TOKEN"]

    response = client.post(
        "/bridge/plan",
        json={
            "identity": "EchoWildfire",
            "cycle": "11",
            "signature": "eden88::cycle11",
            "traits": {"pulse": "aurora"},
            "summary": "Cycle 11 bridge update",
            "links": ["https://echo.example/cycles/11", " https://status.echo/bridge "],
            "topics": ["Echo Bridge", "pulse orbit", "Echo Bridge"],
            "priority": "major",
        },
    )

    assert response.status_code == 200
    plans = {plan["platform"]: plan for plan in response.json()["plans"]}

    discussion = plans["github_discussions"]
    assert discussion["action"] == "create_discussion"
    assert discussion["payload"]["repo"] == "sovereign"
    assert discussion["payload"]["category"] == "Bridge Updates"
    assert discussion["payload"]["context"]["cycle"] == "11"
    assert "Echo Bridge Relay" in discussion["payload"]["body"]
    assert discussion["requires_secret"] == ["ECHO_DISCUSS_TOKEN"]

    rss = plans["rss"]
    assert rss["action"] == "publish_entry"
    assert rss["payload"]["feed_url"] == "https://echo.example/feed.xml"
    assert rss["payload"]["entry"]["title"] == "Echo Relay EchoWildfire/11"
    assert rss["payload"]["entry"]["links"] == [
        "https://echo.example/cycles/11",
        "https://status.echo/bridge",
    ]
    assert rss["payload"]["entry"]["topics"] == ["Echo Bridge", "pulse orbit"]
    assert rss["payload"]["entry"]["priority"] == "major"
    assert rss["requires_secret"] == ["ECHO_RSS_TOKEN"]


def test_router_factory_uses_environment_defaults(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ECHO_BRIDGE_STATE_DIR", str(tmp_path / "bridge"))
    monkeypatch.setenv("ECHO_BRIDGE_GITHUB_REPOSITORY", "EchoOrg/sovereign")
    monkeypatch.setenv(
        "ECHO_BRIDGE_SLACK_WEBHOOK_URL",
        "https://hooks.slack.com/services/T000/B000/XXXX",
    )
    monkeypatch.setenv("ECHO_BRIDGE_SLACK_SECRET", "SLACK_ECHO_WEBHOOK")
    monkeypatch.setenv("ECHO_BRIDGE_WEBHOOK_URL", "https://bridge.echo/webhook")
    monkeypatch.setenv("ECHO_BRIDGE_UNSTOPPABLE_DOMAINS", "echo.crypto,nexus.crypto")
    monkeypatch.setenv("ECHO_BRIDGE_VERCEL_PROJECTS", "console")

    app = FastAPI()
    app.include_router(create_router())
    client = TestClient(app)

    response = client.get("/bridge/relays", params={"include_sync": True})
    assert response.status_code == 200
    payload = response.json()

    connectors = {connector["platform"] for connector in payload["connectors"]}
    assert {"github", "slack", "webhook", "unstoppable", "vercel"} <= connectors

    sync_connectors = {connector["platform"] for connector in payload["sync_connectors"]}
    assert {"github", "unstoppable", "vercel"} <= sync_connectors


def test_netlify_deploy_hook_handles_missing_environment(monkeypatch) -> None:
    monkeypatch.delenv("ECHO_BRIDGE_NETLIFY_DEPLOY_HOOK", raising=False)
    monkeypatch.setenv("ECHO_BRIDGE_GITHUB_REPOSITORY", "EchoOrg/sovereign")

    app = FastAPI()
    app.include_router(create_router())
    client = TestClient(app)

    response = client.get("/bridge/relays")
    assert response.status_code == 200

    connectors = {connector["platform"] for connector in response.json()["connectors"]}
    assert "netlify" not in connectors


def test_vercel_deploy_hook_handles_missing_environment(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("ECHO_BRIDGE_VERCEL_PROJECTS", raising=False)

    service = BridgeSyncService.from_environment(
        state_dir=tmp_path,
        github_repository="EchoOrg/sovereign",
    )

    decision = {
        "inputs": {
            "cycle_digest": {"cycle": "11"},
            "registrations": [{"unstoppable_domains": ["echo.crypto"]}],
        },
        "coherence": {"score": 0.88},
        "manifest": {"path": "manifest/c11.json"},
    }

    operations = service.sync(decision)
    connectors = {operation["connector"] for operation in operations}
    assert "vercel" not in connectors
    assert "unstoppable" in connectors


def test_api_module_respects_bridge_state_dir(monkeypatch, tmp_path) -> None:
    bridge_state = tmp_path / "bridge-state"
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("ECHO_BRIDGE_STATE_DIR", str(bridge_state))
    monkeypatch.setenv("ECHO_STATE_ROOT", str(state_root))
    monkeypatch.setenv("ECHO_BRIDGE_GITHUB_REPOSITORY", "EchoOrg/sovereign")

    import importlib
    import sys

    sys.modules.pop("echo.api", None)
    api = importlib.import_module("echo.api")

    try:
        assert api._bridge_sync_service.log_path.parent == bridge_state
    finally:
        sys.modules.pop("echo.api", None)


def test_secrets_endpoint_reports_availability(monkeypatch) -> None:
    app = _make_app()
    client = TestClient(app)

    monkeypatch.setenv("SLACK_ECHO_WEBHOOK", "present")
    monkeypatch.setenv("ECHO_ACTIVITYPUB_SECRET", "present")

    response = client.get("/bridge/secrets")
    assert response.status_code == 200
    payload = response.json()

    secrets = {item["name"]: item["available"] for item in payload["secrets"]}
    assert secrets["SLACK_ECHO_WEBHOOK"] is True
    assert secrets["ECHO_ACTIVITYPUB_SECRET"] is True
