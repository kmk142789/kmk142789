"""FastAPI router exposing the Echo Bridge relay planner and sync history."""

from __future__ import annotations

import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from . import EchoBridgeAPI, BridgePlan
from .models import (
    ConnectorDescriptor,
    PlanModel,
    PlanRequest,
    PlanResponse,
    SecretStatusEntry,
    SecretStatusResponse,
    StatusResponse,
    SyncLogEntry,
    SyncRequest,
    SyncResponse,
    SyncStats,
)
from .service import BridgeSyncService


def _parse_recipients_env(value: Optional[str]) -> List[str] | None:
    if not value:
        return None
    entries = [item.strip() for item in value.split(",") if item.strip()]
    return entries or None


def _parse_float_env(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def _bridge_api_factory() -> EchoBridgeAPI:
    """Instantiate an ``EchoBridgeAPI`` using environment defaults."""

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
        bluesky_app_password_secret=os.getenv(
            "ECHO_BRIDGE_BLUESKY_SECRET", "BLUESKY_APP_PASSWORD"
        ),
        mastodon_instance_url=os.getenv("ECHO_BRIDGE_MASTODON_INSTANCE"),
        mastodon_visibility=os.getenv("ECHO_BRIDGE_MASTODON_VISIBILITY", "unlisted"),
        mastodon_secret_name=os.getenv("ECHO_BRIDGE_MASTODON_SECRET", "MASTODON_ACCESS_TOKEN"),
        matrix_homeserver=os.getenv("ECHO_BRIDGE_MATRIX_HOMESERVER"),
        matrix_room_id=os.getenv("ECHO_BRIDGE_MATRIX_ROOM_ID"),
        matrix_secret_name=os.getenv("ECHO_BRIDGE_MATRIX_SECRET", "MATRIX_ACCESS_TOKEN"),
        activitypub_inbox_url=os.getenv("ECHO_BRIDGE_ACTIVITYPUB_INBOX"),
        activitypub_actor=os.getenv("ECHO_BRIDGE_ACTIVITYPUB_ACTOR"),
        activitypub_secret_name=os.getenv(
            "ECHO_BRIDGE_ACTIVITYPUB_SECRET", "ACTIVITYPUB_SIGNING_KEY"
        ),
        teams_webhook_url=os.getenv("ECHO_BRIDGE_TEAMS_WEBHOOK_URL"),
        teams_secret_name=os.getenv("ECHO_BRIDGE_TEAMS_SECRET", "TEAMS_WEBHOOK_URL"),
        farcaster_identity=os.getenv("ECHO_BRIDGE_FARCASTER_IDENTITY"),
        farcaster_secret_name=os.getenv(
            "ECHO_BRIDGE_FARCASTER_SECRET", "FARCASTER_SIGNING_KEY"
        ),
        nostr_relays=_parse_recipients_env(os.getenv("ECHO_BRIDGE_NOSTR_RELAYS")),
        nostr_public_key=os.getenv("ECHO_BRIDGE_NOSTR_PUBLIC_KEY"),
        nostr_secret_name=os.getenv("ECHO_BRIDGE_NOSTR_SECRET", "NOSTR_PRIVATE_KEY"),
        sms_recipients=_parse_recipients_env(os.getenv("ECHO_BRIDGE_SMS_RECIPIENTS")),
        sms_secret_name=os.getenv("ECHO_BRIDGE_SMS_SECRET", "TWILIO_AUTH_TOKEN"),
        sms_from_number=os.getenv("ECHO_BRIDGE_SMS_FROM_NUMBER"),
        statuspage_page_id=os.getenv("ECHO_BRIDGE_STATUSPAGE_PAGE_ID"),
        statuspage_secret_name=os.getenv(
            "ECHO_BRIDGE_STATUSPAGE_SECRET", "STATUSPAGE_API_TOKEN"
        ),
        email_recipients=_parse_recipients_env(os.getenv("ECHO_BRIDGE_EMAIL_RECIPIENTS")),
        email_secret_name=os.getenv("ECHO_BRIDGE_EMAIL_SECRET", "EMAIL_RELAY_API_KEY"),
        email_subject_template=os.getenv(
            "ECHO_BRIDGE_EMAIL_SUBJECT_TEMPLATE",
            "Echo Identity Relay :: {identity} :: Cycle {cycle}",
        ),
        notion_database_id=os.getenv("ECHO_BRIDGE_NOTION_DATABASE_ID"),
        notion_secret_name=os.getenv("ECHO_BRIDGE_NOTION_SECRET", "NOTION_API_KEY"),
        dns_root_domain=os.getenv("ECHO_BRIDGE_DNS_ROOT_DOMAIN"),
        dns_additional_root_domains=_parse_recipients_env(
            os.getenv("ECHO_BRIDGE_DNS_ADDITIONAL_ROOT_DOMAINS")
        ),
        dns_record_prefix=os.getenv("ECHO_BRIDGE_DNS_RECORD_PREFIX", "_echo"),
        dns_provider=os.getenv("ECHO_BRIDGE_DNS_PROVIDER"),
        dns_secret_name=os.getenv("ECHO_BRIDGE_DNS_SECRET", "DNS_PROVIDER_TOKEN"),
        dns_root_authority=os.getenv("ECHO_BRIDGE_DNS_ROOT_AUTHORITY"),
        dns_attestation_path=os.getenv("ECHO_BRIDGE_DNS_ATTESTATION_PATH"),
        unstoppable_domains=_parse_recipients_env(os.getenv("ECHO_BRIDGE_UNSTOPPABLE_DOMAINS")),
        unstoppable_secret_name=os.getenv("ECHO_BRIDGE_UNSTOPPABLE_SECRET", "UNSTOPPABLE_API_TOKEN"),
        vercel_projects=_parse_recipients_env(os.getenv("ECHO_BRIDGE_VERCEL_PROJECTS")),
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
        tcp_endpoints=_parse_recipients_env(os.getenv("ECHO_BRIDGE_TCP_ENDPOINTS")),
        tcp_secret_name=os.getenv("ECHO_BRIDGE_TCP_SECRET", "TCP_RELAY_TOKEN"),
        iot_channel=os.getenv("ECHO_BRIDGE_IOT_CHANNEL"),
        iot_secret_name=os.getenv("ECHO_BRIDGE_IOT_SECRET", "IOT_RELAY_TOKEN"),
        kafka_topic=os.getenv("ECHO_BRIDGE_KAFKA_TOPIC"),
        kafka_bootstrap_servers=_parse_recipients_env(
            os.getenv("ECHO_BRIDGE_KAFKA_BOOTSTRAP_SERVERS")
        ),
        kafka_secret_name=os.getenv("ECHO_BRIDGE_KAFKA_SECRET", "KAFKA_RELAY_TOKEN"),
        wifi_ssid=os.getenv("ECHO_BRIDGE_WIFI_SSID"),
        wifi_channel=os.getenv("ECHO_BRIDGE_WIFI_CHANNEL"),
        wifi_bandwidth_mhz=_parse_float_env(os.getenv("ECHO_BRIDGE_WIFI_BANDWIDTH_MHZ")),
        wifi_frequency_mhz=_parse_float_env(os.getenv("ECHO_BRIDGE_WIFI_FREQUENCY_MHZ")),
        bluetooth_beacon_id=os.getenv("ECHO_BRIDGE_BLUETOOTH_BEACON_ID"),
        bluetooth_profile=os.getenv("ECHO_BRIDGE_BLUETOOTH_PROFILE"),
        bluetooth_bandwidth_mhz=_parse_float_env(
            os.getenv("ECHO_BRIDGE_BLUETOOTH_BANDWIDTH_MHZ")
        ),
        bluetooth_frequency_mhz=_parse_float_env(
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


def _as_plan_model(plan: BridgePlan) -> PlanModel:
    """Convert a legacy dataclass plan into a serialisable model."""

    return PlanModel(
        platform=plan.platform,
        action=plan.action,
        payload=plan.payload,
        requires_secret=list(plan.requires_secret),
    )


def _discover_connectors(api: EchoBridgeAPI) -> List[ConnectorDescriptor]:
    """Return connector descriptions for the configured bridge."""

    connectors: List[ConnectorDescriptor] = []
    if api.github_repository:
        connectors.append(
            ConnectorDescriptor(
                platform="github",
                action="create_issue",
                requires_secrets=["GITHUB_TOKEN"],
            )
        )
    if getattr(api, "github_discussions_repository", None):
        connectors.append(
            ConnectorDescriptor(
                platform="github_discussions",
                action="create_discussion",
                requires_secrets=[api.github_discussions_secret_name]
                if getattr(api, "github_discussions_secret_name", None)
                else [],
            )
        )
    if api.telegram_chat_id:
        connectors.append(
            ConnectorDescriptor(
                platform="telegram",
                action="send_message",
                requires_secrets=["TELEGRAM_BOT_TOKEN"],
            )
        )
    if api.firebase_collection:
        connectors.append(
            ConnectorDescriptor(
                platform="firebase",
                action="set_document",
                requires_secrets=["FIREBASE_SERVICE_ACCOUNT"],
            )
        )
    if api.slack_webhook_url:
        connectors.append(
            ConnectorDescriptor(
                platform="slack",
                action="send_webhook",
                requires_secrets=[api.slack_secret_name] if api.slack_secret_name else [],
            )
        )
    if api.webhook_url:
        connectors.append(
            ConnectorDescriptor(
                platform="webhook",
                action="post_json",
                requires_secrets=[api.webhook_secret_name] if api.webhook_secret_name else [],
            )
        )
    if getattr(api, "tcp_endpoints", None):
        connectors.append(
            ConnectorDescriptor(
                platform="tcp",
                action="send_payload",
                requires_secrets=[api.tcp_secret_name] if getattr(api, "tcp_secret_name", None) else [],
            )
        )
    if getattr(api, "iot_channel", None):
        connectors.append(
            ConnectorDescriptor(
                platform="iot",
                action="publish",
                requires_secrets=[api.iot_secret_name] if getattr(api, "iot_secret_name", None) else [],
            )
        )
    if getattr(api, "kafka_topic", None):
        connectors.append(
            ConnectorDescriptor(
                platform="kafka",
                action="publish_event",
                requires_secrets=[api.kafka_secret_name]
                if getattr(api, "kafka_secret_name", None)
                else [],
            )
        )
    if getattr(api, "s3_bucket", None):
        connectors.append(
            ConnectorDescriptor(
                platform="s3",
                action="write_object",
                requires_secrets=[api.s3_secret_name]
                if getattr(api, "s3_secret_name", None)
                else [],
            )
        )
    if getattr(api, "wifi_ssid", None):
        connectors.append(
            ConnectorDescriptor(
                platform="wifi",
                action="broadcast_frame",
                requires_secrets=[],
            )
        )
    if getattr(api, "bluetooth_beacon_id", None):
        connectors.append(
            ConnectorDescriptor(
                platform="bluetooth",
                action="emit_beacon",
                requires_secrets=[],
            )
        )
    if getattr(api, "arweave_gateway_url", None):
        connectors.append(
            ConnectorDescriptor(
                platform="arweave",
                action="submit_transaction",
                requires_secrets=
                [api.arweave_wallet_secret_name]
                if getattr(api, "arweave_wallet_secret_name", None)
                else [],
            )
        )
    if getattr(api, "rss_feed_url", None):
        connectors.append(
            ConnectorDescriptor(
                platform="rss",
                action="publish_entry",
                requires_secrets=[api.rss_secret_name] if api.rss_secret_name else [],
            )
        )
    if api.discord_webhook_url:
        connectors.append(
            ConnectorDescriptor(
                platform="discord",
                action="send_webhook",
                requires_secrets=[api.discord_secret_name] if api.discord_secret_name else [],
            )
        )
    if getattr(api, "bluesky_identifier", None):
        connectors.append(
            ConnectorDescriptor(
                platform="bluesky",
                action="post_record",
                requires_secrets=[api.bluesky_app_password_secret]
                if getattr(api, "bluesky_app_password_secret", None)
                else [],
            )
        )
    if getattr(api, "email_recipients", None):
        connectors.append(
            ConnectorDescriptor(
                platform="email",
                action="send_email",
                requires_secrets=[api.email_secret_name] if api.email_secret_name else [],
            )
        )
    if getattr(api, "mastodon_instance_url", None):
        connectors.append(
            ConnectorDescriptor(
                platform="mastodon",
                action="post_status",
                requires_secrets=[api.mastodon_secret_name] if api.mastodon_secret_name else [],
            )
        )
    if getattr(api, "notion_database_id", None):
        connectors.append(
            ConnectorDescriptor(
                platform="notion",
                action="create_page",
                requires_secrets=[api.notion_secret_name] if api.notion_secret_name else [],
            )
        )
    if getattr(api, "activitypub_inbox_url", None):
        connectors.append(
            ConnectorDescriptor(
                platform="activitypub",
                action="deliver_note",
                requires_secrets=[api.activitypub_secret_name]
                if getattr(api, "activitypub_secret_name", None)
                else [],
            )
        )
    if getattr(api, "dns_root_domain", None) or getattr(
        api, "dns_additional_root_domains", None
    ):
        connectors.append(
            ConnectorDescriptor(
                platform="dns",
                action="upsert_txt_record",
                requires_secrets=[api.dns_secret_name] if getattr(api, "dns_secret_name", None) else [],
            )
        )
    if getattr(api, "unstoppable_domains", None):
        connectors.append(
            ConnectorDescriptor(
                platform="unstoppable",
                action="update_domain_records",
                requires_secrets=[api.unstoppable_secret_name]
                if getattr(api, "unstoppable_secret_name", None)
                else [],
            )
        )
    if getattr(api, "vercel_projects", None):
        connectors.append(
            ConnectorDescriptor(
                platform="vercel",
                action="trigger_deploy",
                requires_secrets=[api.vercel_secret_name]
                if getattr(api, "vercel_secret_name", None)
                else [],
            )
        )
    if getattr(api, "teams_webhook_url", None):
        connectors.append(
            ConnectorDescriptor(
                platform="teams",
                action="send_webhook",
                requires_secrets=[api.teams_secret_name] if api.teams_secret_name else [],
            )
        )
    if getattr(api, "matrix_homeserver", None) and getattr(api, "matrix_room_id", None):
        connectors.append(
            ConnectorDescriptor(
                platform="matrix",
                action="send_room_message",
                requires_secrets=[api.matrix_secret_name] if api.matrix_secret_name else [],
            )
        )
    if getattr(api, "farcaster_identity", None):
        connectors.append(
            ConnectorDescriptor(
                platform="farcaster",
                action="post_cast",
                requires_secrets=[api.farcaster_secret_name]
                if getattr(api, "farcaster_secret_name", None)
                else [],
            )
        )
    if getattr(api, "nostr_relays", None) and getattr(api, "nostr_public_key", None):
        connectors.append(
            ConnectorDescriptor(
                platform="nostr",
                action="post_event",
                requires_secrets=[api.nostr_secret_name] if getattr(api, "nostr_secret_name", None) else [],
            )
        )
    if getattr(api, "sms_recipients", None):
        connectors.append(
            ConnectorDescriptor(
                platform="sms",
                action="send_sms",
                requires_secrets=[api.sms_secret_name] if getattr(api, "sms_secret_name", None) else [],
            )
        )
    if getattr(api, "statuspage_page_id", None):
        connectors.append(
            ConnectorDescriptor(
                platform="statuspage",
                action="create_incident",
                requires_secrets=[api.statuspage_secret_name]
                if getattr(api, "statuspage_secret_name", None)
                else [],
            )
        )
    if getattr(api, "linkedin_organization_id", None):
        connectors.append(
            ConnectorDescriptor(
                platform="linkedin",
                action="create_share",
                requires_secrets=[api.linkedin_secret_name]
                if getattr(api, "linkedin_secret_name", None)
                else [],
            )
        )
    if getattr(api, "reddit_subreddit", None):
        connectors.append(
            ConnectorDescriptor(
                platform="reddit",
                action="submit_post",
                requires_secrets=[api.reddit_secret_name]
                if getattr(api, "reddit_secret_name", None)
                else [],
            )
        )
    if getattr(api, "pagerduty_routing_key_secret", None):
        connectors.append(
            ConnectorDescriptor(
                platform="pagerduty",
                action="trigger_event",
                requires_secrets=[api.pagerduty_routing_key_secret],
            )
        )
    if getattr(api, "opsgenie_api_key_secret", None):
        connectors.append(
            ConnectorDescriptor(
                platform="opsgenie",
                action="create_alert",
                requires_secrets=[api.opsgenie_api_key_secret],
            )
        )
    return connectors


def _collect_required_secrets(
    api: EchoBridgeAPI,
    sync_service: BridgeSyncService | None,
) -> list[SecretStatusEntry]:
    secrets: set[str] = set()
    for connector in _discover_connectors(api):
        secrets.update(connector.requires_secrets)
    if sync_service is not None:
        for descriptor in sync_service.describe_connectors():
            secrets.update(descriptor.get("requires_secrets") or [])

    entries: list[SecretStatusEntry] = []
    for name in sorted(filter(None, secrets)):
        entries.append(SecretStatusEntry(name=name, available=bool(os.getenv(name))))
    return entries


def create_router(
    api: EchoBridgeAPI | None = None,
    sync_service: BridgeSyncService | None = None,
) -> APIRouter:
    """Create a router that exposes bridge planning and sync endpoints."""

    router = APIRouter(prefix="/bridge", tags=["bridge"])
    api = api or _bridge_api_factory()
    sync_service = sync_service or BridgeSyncService.from_environment(
        github_repository=api.github_repository
    )

    @router.get("/relays", response_model=StatusResponse)
    def list_relays(
        bridge: EchoBridgeAPI = Depends(lambda: api),
        include_sync: bool = Query(
            False,
            description=(
                "When true, include sync connector metadata alongside planner connectors."
            ),
        ),
    ) -> StatusResponse:
        """Return the connectors that are ready for relay planning."""

        connectors = _discover_connectors(bridge)
        if not connectors:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No bridge connectors are currently configured.",
            )
        sync_connectors = None
        if include_sync:
            sync_connectors = [
                ConnectorDescriptor(
                    platform=descriptor.get("platform", "unknown"),
                    action=descriptor.get("action", ""),
                    requires_secrets=list(descriptor.get("requires_secrets") or []),
                )
                for descriptor in sync_service.describe_connectors()
            ]
        return StatusResponse(connectors=connectors, sync_connectors=sync_connectors)

    @router.get("/secrets", response_model=SecretStatusResponse)
    def list_secrets(
        include_sync: bool = Query(
            True,
            description="When true, include secrets required by sync connectors.",
        ),
    ) -> SecretStatusResponse:
        """Return required secret identifiers and availability in the environment."""

        secrets = _collect_required_secrets(api, sync_service if include_sync else None)
        return SecretStatusResponse(secrets=secrets)

    @router.post("/plan", response_model=PlanResponse)
    def plan_relay(
        request: PlanRequest,
        bridge: EchoBridgeAPI = Depends(lambda: api),
    ) -> PlanResponse:
        """Generate relay instructions for the provided identity."""

        plans = bridge.plan_identity_relay(
            identity=request.identity,
            cycle=request.cycle,
            signature=request.signature,
            traits=request.traits,
            summary=request.summary,
            links=request.links,
            topics=request.topics,
            priority=request.priority,
            connectors=request.connectors,
        )
        if not plans:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Bridge connectors are not available for planning.",
        )
        return PlanResponse(plans=[_as_plan_model(plan) for plan in plans])

    @router.get("/sync", response_model=SyncResponse)
    def sync_history(
        limit: int = Query(10, ge=1, le=200),
        connector: str | None = Query(
            None,
            min_length=1,
            description="Optional connector name to filter sync operations by.",
        ),
        include_stats: bool = Query(
            False,
            description="When true, include aggregate metrics for the returned history entries.",
        ),
        service: BridgeSyncService = Depends(lambda: sync_service),
    ) -> SyncResponse:
        """Return historical sync operations generated by the orchestrator."""

        entries = service.history(limit=limit, connector=connector)
        latest_cycle = entries[-1].get("cycle") if entries else None
        stats = SyncStats(**service.summarize(entries)) if include_stats and entries else None
        operations = [SyncLogEntry(**entry) for entry in entries]
        return SyncResponse(cycle=latest_cycle, operations=operations, stats=stats)

    @router.post("/sync", response_model=SyncResponse, status_code=status.HTTP_201_CREATED)
    def record_sync(
        decision: dict[str, object],
        connectors: list[str] | None = None,
        include_stats: bool = Query(
            False,
            description="When true, include aggregate metrics for the new sync run.",
        ),
        service: BridgeSyncService = Depends(lambda: sync_service),
    ) -> SyncResponse:
        """Execute a sync against the provided decision and persist the results."""

        sync_request = SyncRequest(decision=decision, connectors=connectors)
        operations = service.sync(
            sync_request.decision, only_connectors=sync_request.connectors
        )
        latest_cycle = operations[-1].get("cycle") if operations else None
        stats = SyncStats(**service.summarize(operations)) if include_stats and operations else None
        payload = [SyncLogEntry(**entry) for entry in operations]
        return SyncResponse(cycle=latest_cycle, operations=payload, stats=stats)

    return router


__all__ = ["create_router"]
