"""Echo API application."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Optional

from fastapi import FastAPI, HTTPException

from echo.bridge import BridgeSyncService, EchoBridgeAPI
from echo.bridge.router import create_router as create_bridge_router
from echo.echoforge.api import create_router as create_echoforge_router
from echo.echoforge.service import EchoForgeDashboardService
from echo.echoforge.storage import EchoForgeSessionStore
from echo.deployment_meta_causal import (
    CONFIG_PATH as META_CAUSAL_CONFIG_PATH,
    load_meta_causal_config,
    plan_meta_causal_deployment,
    save_meta_causal_config,
)
from echo.pulsenet import AtlasAttestationResolver, PulseNetGatewayService
from echo.pulsenet.api import create_router as create_pulsenet_router
from echo.pulsenet.registration import RegistrationStore
from echo.pulsenet.stream import PulseAttestor, PulseHistoryStreamer
from echo.resonance import HarmonicsAI
from echo.evolver import EchoEvolver
from echo_atlas.api import create_router as create_atlas_router
from echo_atlas.service import AtlasService
from pulse_weaver.api import create_router as create_pulse_weaver_router
from pulse_weaver.service import PulseWeaverService

from .routes_echonet import router as echonet_router
from .routes_registry import router as registry_router
from .routes_timeline import router as timeline_router
from .state import dag, receipts, session_heads, set_dag, set_receipts, set_session_heads
from echo.atlas.temporal_ledger import TemporalLedger
from echo.pulseweaver import build_pulse_bus, build_watchdog
from echo.pulseweaver.api import create_router as create_pulse_router
from echo.pulseweaver.fabric import FabricOperations
from echo.orchestrator.core import OrchestratorCore
from echo.orchestrator.api import create_router as create_orchestrator_router
from echo.semantic_negotiation import SemanticNegotiationResolver

app = FastAPI(title="Echo")
app.include_router(echonet_router)
app.include_router(registry_router)
app.include_router(timeline_router)

def _parse_recipients_env(value: Optional[str]) -> list[str] | None:
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


_bridge_api = EchoBridgeAPI(
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
    nostr_relays=_parse_recipients_env(os.getenv("ECHO_BRIDGE_NOSTR_RELAYS")),
    nostr_public_key=os.getenv("ECHO_BRIDGE_NOSTR_PUBLIC_KEY"),
    nostr_secret_name=os.getenv("ECHO_BRIDGE_NOSTR_SECRET", "NOSTR_PRIVATE_KEY"),
    sms_recipients=_parse_recipients_env(os.getenv("ECHO_BRIDGE_SMS_RECIPIENTS")),
    sms_secret_name=os.getenv("ECHO_BRIDGE_SMS_SECRET", "TWILIO_AUTH_TOKEN"),
    sms_from_number=os.getenv("ECHO_BRIDGE_SMS_FROM_NUMBER"),
    statuspage_page_id=os.getenv("ECHO_BRIDGE_STATUSPAGE_PAGE_ID"),
    statuspage_secret_name=os.getenv("ECHO_BRIDGE_STATUSPAGE_SECRET", "STATUSPAGE_API_TOKEN"),
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
    unstoppable_secret_name=os.getenv(
        "ECHO_BRIDGE_UNSTOPPABLE_SECRET", "UNSTOPPABLE_API_TOKEN"
    ),
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
    arweave_gateway_url=os.getenv("ECHO_BRIDGE_ARWEAVE_GATEWAY"),
    arweave_wallet_secret_name=os.getenv(
        "ECHO_BRIDGE_ARWEAVE_SECRET", "ARWEAVE_WALLET_JWK"
    ),
)
_state_root = Path(os.getenv("ECHO_STATE_ROOT", str(Path.cwd() / "state")))
_bridge_state_dir_env = os.getenv("ECHO_BRIDGE_STATE_DIR")
_bridge_state_dir = (
    Path(_bridge_state_dir_env)
    if _bridge_state_dir_env
    else _state_root / "bridge"
)
_bridge_state_dir.mkdir(parents=True, exist_ok=True)
_bridge_sync_service = BridgeSyncService.from_environment(
    state_dir=_bridge_state_dir,
    github_repository=_bridge_api.github_repository,
)
app.include_router(create_bridge_router(api=_bridge_api, sync_service=_bridge_sync_service))

_atlas_service = AtlasService(Path.cwd())
_atlas_service.ensure_ready()
app.include_router(create_atlas_router(_atlas_service))

_pulse_weaver_service = PulseWeaverService(Path.cwd())
_pulse_weaver_service.ensure_ready()
app.include_router(create_pulse_weaver_router(_pulse_weaver_service))

_pulse_state = _state_root
_pulse_watchdog = build_watchdog(_pulse_state)
_pulse_bus = build_pulse_bus(_pulse_state)
_pulse_ledger = TemporalLedger(state_dir=_pulse_state)
_fabric_ops = FabricOperations(_pulse_state)
app.include_router(
    create_pulse_router(
        _pulse_watchdog,
        _pulse_bus,
        _pulse_ledger,
        fabric_ops=_fabric_ops,
    )
)

_pulsenet_state = _state_root / "pulsenet"
_pulsenet_state.mkdir(parents=True, exist_ok=True)
_pulsenet_store = RegistrationStore(_pulsenet_state / "registrations.json")
_pulsenet_stream = PulseHistoryStreamer(Path.cwd() / "pulse_history.json")
_pulsenet_attestor = PulseAttestor(TemporalLedger(state_dir=_pulsenet_state))
_pulsenet_atlas_resolver = AtlasAttestationResolver(Path.cwd(), _atlas_service)
_pulsenet_service = PulseNetGatewayService(
    project_root=Path.cwd(),
    registration_store=_pulsenet_store,
    pulse_streamer=_pulsenet_stream,
    attestor=_pulsenet_attestor,
    atlas_service=_atlas_service,
    resolver_config=_pulsenet_state / "resolver_sources.json",
    atlas_resolver=_pulsenet_atlas_resolver,
)
app.include_router(create_pulsenet_router(_pulsenet_service))

_echoforge_state = _state_root / "echoforge"
_echoforge_state.mkdir(parents=True, exist_ok=True)
_echoforge_sessions = EchoForgeSessionStore(_echoforge_state / "sessions.sqlite3")
_echoforge_frontend = Path(__file__).resolve().parent.parent / "echoforge" / "frontend" / "index.html"
_echoforge_service = EchoForgeDashboardService(
    project_root=Path.cwd(),
    pulsenet=_pulsenet_service,
    session_store=_echoforge_sessions,
    atlas_resolver=_pulsenet_atlas_resolver,
    frontend_path=_echoforge_frontend,
)
app.include_router(create_echoforge_router(_echoforge_service))

_orchestrator_state = _state_root / "orchestrator"
_orchestrator_state.mkdir(parents=True, exist_ok=True)
_negotiation_state = _orchestrator_state / "negotiations"
_negotiation_state.mkdir(parents=True, exist_ok=True)
_negotiation_resolver = SemanticNegotiationResolver(state_dir=_negotiation_state)
_orchestrator_service = OrchestratorCore(
    state_dir=_orchestrator_state,
    pulsenet=_pulsenet_service,
    evolver=EchoEvolver(),
    resonance_engine=HarmonicsAI(),
    atlas_resolver=_pulsenet_atlas_resolver,
    bridge_service=_bridge_sync_service,
    negotiation_resolver=_negotiation_resolver,
)
app.include_router(create_orchestrator_router(_orchestrator_service))


@app.post("/deploy/meta-causal-engine", name="deploy_meta_causal_engine")
def deploy_meta_causal_engine(payload: Mapping[str, Any] | None = None) -> MutableMapping[str, Any]:
    data = dict(payload or {})
    updates: MutableMapping[str, object] = {}

    status = data.get("status")
    enabled_override: Optional[bool] = None
    if status is not None:
        if not isinstance(status, str):
            raise HTTPException(status_code=400, detail="status must be a string")
        normalised = status.strip().lower()
        if normalised not in {"enabled", "disabled"}:
            raise HTTPException(status_code=400, detail="status must be 'enabled' or 'disabled'")
        enabled_override = normalised == "enabled"
        updates["status"] = normalised

    channel = data.get("channel")
    channel_override: Optional[str] = None
    if channel is not None:
        if not isinstance(channel, str):
            raise HTTPException(status_code=400, detail="channel must be a string")
        channel_override = channel
        updates["channel"] = channel_override

    max_parallel_raw = data.get("max_parallel")
    max_parallel_override: Optional[int] = None
    if max_parallel_raw is not None:
        if isinstance(max_parallel_raw, bool) or not isinstance(max_parallel_raw, int):
            raise HTTPException(status_code=400, detail="max_parallel must be an integer")
        if max_parallel_raw < 1:
            raise HTTPException(status_code=400, detail="max_parallel must be >= 1")
        max_parallel_override = max_parallel_raw
        updates["max_parallel"] = max_parallel_override

    reason = data.get("reason")
    if reason is not None and not isinstance(reason, str):
        raise HTTPException(status_code=400, detail="reason must be a string")

    apply_changes = bool(data.get("apply", False))

    config = load_meta_causal_config().with_overrides(
        enabled=enabled_override,
        channel=channel_override,
        max_parallel=max_parallel_override,
    )
    plan = plan_meta_causal_deployment(
        config,
        initiated_by="echo-api",
        reason=reason,
    )
    plan["config_path"] = str(META_CAUSAL_CONFIG_PATH)
    if updates:
        plan["updates"] = dict(updates)

    response: MutableMapping[str, Any] = {"plan": plan, "applied": False}
    if apply_changes:
        save_meta_causal_config(config)
        response["applied"] = True
    return response


__all__ = [
    "app",
    "dag",
    "receipts",
    "session_heads",
    "set_dag",
    "set_receipts",
    "set_session_heads",
]
