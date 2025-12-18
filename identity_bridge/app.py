"""Development ASGI application exposing the Echo identity bridge router."""
from __future__ import annotations

import os
from functools import lru_cache
from importlib import import_module
from typing import Optional

from fastapi import FastAPI

from echo.bridge.router import create_router

BridgeModule = import_module("modules.echo-bridge.bridge_api")
EchoBridgeAPI = BridgeModule.EchoBridgeAPI


def _parse_recipients(value: Optional[str]) -> list[str] | None:
    if not value:
        return None
    entries = [item.strip() for item in value.split(",") if item.strip()]
    return entries or None


def _parse_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


@lru_cache(maxsize=1)
def _build_bridge_api() -> EchoBridgeAPI:
    """Create an :class:`EchoBridgeAPI` using environment configuration."""

    return EchoBridgeAPI(
        github_repository=os.getenv("ECHO_BRIDGE_GITHUB_REPOSITORY"),
        github_discussions_repository=os.getenv("ECHO_BRIDGE_GITHUB_DISCUSSIONS_REPOSITORY"),
        github_discussion_category=os.getenv(
            "ECHO_BRIDGE_GITHUB_DISCUSSION_CATEGORY", "Announcements"
        ),
        github_discussions_secret_name=os.getenv(
            "ECHO_BRIDGE_GITHUB_DISCUSSIONS_SECRET", "GITHUB_TOKEN"
        ),
        telegram_chat_id=os.getenv("ECHO_BRIDGE_TELEGRAM_CHAT_ID"),
        firebase_collection=os.getenv("ECHO_BRIDGE_FIREBASE_COLLECTION"),
        slack_webhook_url=os.getenv("ECHO_BRIDGE_SLACK_WEBHOOK_URL"),
        slack_channel=os.getenv("ECHO_BRIDGE_SLACK_CHANNEL"),
        slack_secret_name=os.getenv("ECHO_BRIDGE_SLACK_SECRET", "SLACK_WEBHOOK_URL"),
        webhook_url=os.getenv("ECHO_BRIDGE_WEBHOOK_URL"),
        webhook_secret_name=os.getenv("ECHO_BRIDGE_WEBHOOK_SECRET", "ECHO_BRIDGE_WEBHOOK_URL"),
        discord_webhook_url=os.getenv("ECHO_BRIDGE_DISCORD_WEBHOOK_URL"),
        discord_secret_name=os.getenv("ECHO_BRIDGE_DISCORD_SECRET", "DISCORD_WEBHOOK_URL"),
        bluesky_identifier=os.getenv("ECHO_BRIDGE_BLUESKY_IDENTIFIER"),
        bluesky_service_url=os.getenv("ECHO_BRIDGE_BLUESKY_SERVICE", "https://bsky.social"),
        bluesky_app_password_secret=os.getenv("ECHO_BRIDGE_BLUESKY_SECRET", "BLUESKY_APP_PASSWORD"),
        mastodon_instance_url=os.getenv("ECHO_BRIDGE_MASTODON_INSTANCE"),
        mastodon_visibility=os.getenv("ECHO_BRIDGE_MASTODON_VISIBILITY", "unlisted"),
        mastodon_secret_name=os.getenv("ECHO_BRIDGE_MASTODON_SECRET", "MASTODON_ACCESS_TOKEN"),
        matrix_homeserver=os.getenv("ECHO_BRIDGE_MATRIX_HOMESERVER"),
        matrix_room_id=os.getenv("ECHO_BRIDGE_MATRIX_ROOM_ID"),
        matrix_secret_name=os.getenv("ECHO_BRIDGE_MATRIX_SECRET", "MATRIX_ACCESS_TOKEN"),
        activitypub_inbox_url=os.getenv("ECHO_BRIDGE_ACTIVITYPUB_INBOX"),
        activitypub_actor=os.getenv("ECHO_BRIDGE_ACTIVITYPUB_ACTOR"),
        activitypub_secret_name=os.getenv("ECHO_BRIDGE_ACTIVITYPUB_SECRET", "ACTIVITYPUB_SIGNING_KEY"),
        teams_webhook_url=os.getenv("ECHO_BRIDGE_TEAMS_WEBHOOK_URL"),
        teams_secret_name=os.getenv("ECHO_BRIDGE_TEAMS_SECRET", "TEAMS_WEBHOOK_URL"),
        farcaster_identity=os.getenv("ECHO_BRIDGE_FARCASTER_IDENTITY"),
        farcaster_secret_name=os.getenv("ECHO_BRIDGE_FARCASTER_SECRET", "FARCASTER_SIGNING_KEY"),
        nostr_relays=_parse_recipients(os.getenv("ECHO_BRIDGE_NOSTR_RELAYS")),
        nostr_public_key=os.getenv("ECHO_BRIDGE_NOSTR_PUBLIC_KEY"),
        nostr_secret_name=os.getenv("ECHO_BRIDGE_NOSTR_SECRET", "NOSTR_PRIVATE_KEY"),
        sms_recipients=_parse_recipients(os.getenv("ECHO_BRIDGE_SMS_RECIPIENTS")),
        sms_secret_name=os.getenv("ECHO_BRIDGE_SMS_SECRET", "TWILIO_AUTH_TOKEN"),
        sms_from_number=os.getenv("ECHO_BRIDGE_SMS_FROM_NUMBER"),
        statuspage_page_id=os.getenv("ECHO_BRIDGE_STATUSPAGE_PAGE_ID"),
        statuspage_secret_name=os.getenv("ECHO_BRIDGE_STATUSPAGE_SECRET", "STATUSPAGE_API_TOKEN"),
        email_recipients=_parse_recipients(os.getenv("ECHO_BRIDGE_EMAIL_RECIPIENTS")),
        email_secret_name=os.getenv("ECHO_BRIDGE_EMAIL_SECRET", "EMAIL_RELAY_API_KEY"),
        email_subject_template=os.getenv(
            "ECHO_BRIDGE_EMAIL_SUBJECT_TEMPLATE",
            "Echo Identity Relay :: {identity} :: Cycle {cycle}",
        ),
        notion_database_id=os.getenv("ECHO_BRIDGE_NOTION_DATABASE_ID"),
        notion_secret_name=os.getenv("ECHO_BRIDGE_NOTION_SECRET", "NOTION_API_KEY"),
        dns_root_domain=os.getenv("ECHO_BRIDGE_DNS_ROOT_DOMAIN"),
        dns_additional_root_domains=_parse_recipients(
            os.getenv("ECHO_BRIDGE_DNS_ADDITIONAL_ROOT_DOMAINS")
        ),
        dns_record_prefix=os.getenv("ECHO_BRIDGE_DNS_RECORD_PREFIX", "_echo"),
        dns_provider=os.getenv("ECHO_BRIDGE_DNS_PROVIDER"),
        dns_secret_name=os.getenv("ECHO_BRIDGE_DNS_SECRET", "DNS_PROVIDER_TOKEN"),
        dns_root_authority=os.getenv("ECHO_BRIDGE_DNS_ROOT_AUTHORITY"),
        dns_attestation_path=os.getenv("ECHO_BRIDGE_DNS_ATTESTATION_PATH"),
        unstoppable_domains=_parse_recipients(os.getenv("ECHO_BRIDGE_UNSTOPPABLE_DOMAINS")),
        unstoppable_secret_name=os.getenv(
            "ECHO_BRIDGE_UNSTOPPABLE_SECRET", "UNSTOPPABLE_API_TOKEN"
        ),
        vercel_projects=_parse_recipients(os.getenv("ECHO_BRIDGE_VERCEL_PROJECTS")),
        vercel_secret_name=os.getenv("ECHO_BRIDGE_VERCEL_SECRET", "VERCEL_API_TOKEN"),
        linkedin_organization_id=os.getenv("ECHO_BRIDGE_LINKEDIN_ORG"),
        linkedin_secret_name=os.getenv("ECHO_BRIDGE_LINKEDIN_SECRET", "LINKEDIN_ACCESS_TOKEN"),
        reddit_subreddit=os.getenv("ECHO_BRIDGE_REDDIT_SUBREDDIT"),
        reddit_secret_name=os.getenv("ECHO_BRIDGE_REDDIT_SECRET", "REDDIT_APP_TOKEN"),
        rss_feed_url=os.getenv("ECHO_BRIDGE_RSS_FEED_URL"),
        rss_secret_name=os.getenv("ECHO_BRIDGE_RSS_SECRET", "RSS_BRIDGE_TOKEN"),
        pagerduty_routing_key_secret=os.getenv("ECHO_BRIDGE_PAGERDUTY_SECRET"),
        pagerduty_source=os.getenv("ECHO_BRIDGE_PAGERDUTY_SOURCE", "echo-bridge"),
        pagerduty_component=os.getenv("ECHO_BRIDGE_PAGERDUTY_COMPONENT"),
        pagerduty_group=os.getenv("ECHO_BRIDGE_PAGERDUTY_GROUP"),
        opsgenie_api_key_secret=os.getenv("ECHO_BRIDGE_OPSGENIE_SECRET"),
        opsgenie_team=os.getenv("ECHO_BRIDGE_OPSGENIE_TEAM"),
        tcp_endpoints=_parse_recipients(os.getenv("ECHO_BRIDGE_TCP_ENDPOINTS")),
        tcp_secret_name=os.getenv("ECHO_BRIDGE_TCP_SECRET", "TCP_RELAY_TOKEN"),
        iot_channel=os.getenv("ECHO_BRIDGE_IOT_CHANNEL"),
        iot_secret_name=os.getenv("ECHO_BRIDGE_IOT_SECRET", "IOT_RELAY_TOKEN"),
        kafka_topic=os.getenv("ECHO_BRIDGE_KAFKA_TOPIC"),
        kafka_bootstrap_servers=_parse_recipients(
            os.getenv("ECHO_BRIDGE_KAFKA_BOOTSTRAP_SERVERS")
        ),
        kafka_secret_name=os.getenv("ECHO_BRIDGE_KAFKA_SECRET", "KAFKA_RELAY_TOKEN"),
        wifi_ssid=os.getenv("ECHO_BRIDGE_WIFI_SSID"),
        wifi_channel=os.getenv("ECHO_BRIDGE_WIFI_CHANNEL"),
        wifi_bandwidth_mhz=_parse_float(os.getenv("ECHO_BRIDGE_WIFI_BANDWIDTH_MHZ")),
        wifi_frequency_mhz=_parse_float(os.getenv("ECHO_BRIDGE_WIFI_FREQUENCY_MHZ")),
        bluetooth_beacon_id=os.getenv("ECHO_BRIDGE_BLUETOOTH_BEACON_ID"),
        bluetooth_profile=os.getenv("ECHO_BRIDGE_BLUETOOTH_PROFILE"),
        bluetooth_bandwidth_mhz=_parse_float(
            os.getenv("ECHO_BRIDGE_BLUETOOTH_BANDWIDTH_MHZ")
        ),
        bluetooth_frequency_mhz=_parse_float(
            os.getenv("ECHO_BRIDGE_BLUETOOTH_FREQUENCY_MHZ")
        ),
        s3_bucket=os.getenv("ECHO_BRIDGE_S3_BUCKET"),
        s3_prefix=os.getenv("ECHO_BRIDGE_S3_PREFIX"),
        s3_region=os.getenv("ECHO_BRIDGE_S3_REGION"),
        s3_secret_name=os.getenv("ECHO_BRIDGE_S3_SECRET", "S3_RELAY_TOKEN"),
        arweave_gateway_url=os.getenv("ECHO_BRIDGE_ARWEAVE_GATEWAY"),
        arweave_wallet_secret_name=os.getenv(
            "ECHO_BRIDGE_ARWEAVE_SECRET", "ARWEAVE_WALLET_JWK"
        ),
    )


def create_app(*, bridge: Optional[EchoBridgeAPI] = None) -> FastAPI:
    """Instantiate the identity bridge API application."""

    app = FastAPI(title="Identity Bridge", version="0.1.0")
    bridge_api = bridge or _build_bridge_api()
    app.include_router(create_router(api=bridge_api))

    @app.get("/health", tags=["health"])
    async def healthcheck() -> dict[str, str]:  # pragma: no cover - runtime helper
        return {"status": "ok"}

    return app


app = create_app()


__all__ = ["app", "create_app"]
