"""Development ASGI application exposing the Echo identity bridge router."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from fastapi import FastAPI

from echo.bridge.router import create_router
from modules.echo-bridge.bridge_api import EchoBridgeAPI


def _parse_recipients(value: Optional[str]) -> list[str] | None:
    if not value:
        return None
    entries = [item.strip() for item in value.split(",") if item.strip()]
    return entries or None


@lru_cache(maxsize=1)
def _build_bridge_api() -> EchoBridgeAPI:
    """Create an :class:`EchoBridgeAPI` using environment configuration."""

    return EchoBridgeAPI(
        github_repository=os.getenv("ECHO_BRIDGE_GITHUB_REPOSITORY"),
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
        dns_root_domain=os.getenv("ECHO_BRIDGE_DNS_ROOT_DOMAIN"),
        dns_record_prefix=os.getenv("ECHO_BRIDGE_DNS_RECORD_PREFIX", "_echo"),
        dns_provider=os.getenv("ECHO_BRIDGE_DNS_PROVIDER"),
        dns_secret_name=os.getenv("ECHO_BRIDGE_DNS_SECRET", "DNS_PROVIDER_TOKEN"),
        dns_root_authority=os.getenv("ECHO_BRIDGE_DNS_ROOT_AUTHORITY"),
        dns_attestation_path=os.getenv("ECHO_BRIDGE_DNS_ATTESTATION_PATH"),
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
