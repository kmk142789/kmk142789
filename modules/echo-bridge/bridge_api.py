"""Cross-network identity relay planning for Echo."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


@dataclass
class BridgePlan:
    """Declarative instruction describing how to mirror identity state."""

    platform: str
    action: str
    payload: Dict[str, Any]
    requires_secret: List[str] = field(default_factory=list)


@dataclass(slots=True)
class RelayContext:
    """Reusable, normalised state used during plan generation."""

    identity: str
    cycle: str
    signature: str
    traits: Dict[str, Any]
    summary: Optional[str]
    links: List[str]
    topics: List[str]
    priority: Optional[str]
    markdown_body: Optional[str] = None
    plain_text: Optional[str] = None
    social_text: Optional[str] = None
    base_document: Optional[Dict[str, Any]] = None


class EchoBridgeAPI:
    """Plan deterministic Echo identity relays across multiple platforms."""

    def __init__(
        self,
        *,
        github_repository: Optional[str] = None,
        github_discussions_repository: Optional[str] = None,
        github_discussion_category: str = "Announcements",
        github_discussions_secret_name: str = "GITHUB_TOKEN",
        telegram_chat_id: Optional[str] = None,
        firebase_collection: Optional[str] = None,
        slack_webhook_url: Optional[str] = None,
        slack_channel: Optional[str] = None,
        slack_secret_name: str = "SLACK_WEBHOOK_URL",
        webhook_url: Optional[str] = None,
        webhook_secret_name: Optional[str] = "ECHO_BRIDGE_WEBHOOK_URL",
        discord_webhook_url: Optional[str] = None,
        discord_secret_name: str = "DISCORD_WEBHOOK_URL",
        bluesky_identifier: Optional[str] = None,
        bluesky_service_url: str = "https://bsky.social",
        bluesky_app_password_secret: str = "BLUESKY_APP_PASSWORD",
        mastodon_instance_url: Optional[str] = None,
        mastodon_visibility: str = "unlisted",
        mastodon_secret_name: str = "MASTODON_ACCESS_TOKEN",
        matrix_homeserver: Optional[str] = None,
        matrix_room_id: Optional[str] = None,
        matrix_secret_name: str = "MATRIX_ACCESS_TOKEN",
        activitypub_inbox_url: Optional[str] = None,
        activitypub_actor: Optional[str] = None,
        activitypub_secret_name: str = "ACTIVITYPUB_SIGNING_KEY",
        teams_webhook_url: Optional[str] = None,
        teams_secret_name: str = "TEAMS_WEBHOOK_URL",
        farcaster_identity: Optional[str] = None,
        farcaster_secret_name: str = "FARCASTER_SIGNING_KEY",
        nostr_relays: Optional[Sequence[str]] = None,
        nostr_public_key: Optional[str] = None,
        nostr_secret_name: str = "NOSTR_PRIVATE_KEY",
        sms_recipients: Optional[Sequence[str]] = None,
        sms_secret_name: str = "TWILIO_AUTH_TOKEN",
        sms_from_number: Optional[str] = None,
        statuspage_page_id: Optional[str] = None,
        statuspage_secret_name: str = "STATUSPAGE_API_TOKEN",
        email_recipients: Optional[Sequence[str]] = None,
        email_secret_name: Optional[str] = "EMAIL_RELAY_API_KEY",
        email_subject_template: str = "Echo Identity Relay :: {identity} :: Cycle {cycle}",
        notion_database_id: Optional[str] = None,
        notion_secret_name: str = "NOTION_API_KEY",
        dns_root_domain: Optional[str] = None,
        dns_additional_root_domains: Optional[Sequence[str]] = None,
        dns_record_prefix: Optional[str] = "_echo",
        dns_provider: Optional[str] = None,
        dns_secret_name: str = "DNS_PROVIDER_TOKEN",
        dns_root_authority: Optional[str] = None,
        dns_attestation_path: Optional[str] = None,
        unstoppable_domains: Optional[Sequence[str]] = None,
        unstoppable_secret_name: str = "UNSTOPPABLE_API_TOKEN",
        vercel_projects: Optional[Sequence[str]] = None,
        vercel_secret_name: str = "VERCEL_API_TOKEN",
        linkedin_organization_id: Optional[str] = None,
        linkedin_secret_name: str = "LINKEDIN_ACCESS_TOKEN",
        reddit_subreddit: Optional[str] = None,
        reddit_secret_name: str = "REDDIT_APP_TOKEN",
        rss_feed_url: Optional[str] = None,
        rss_secret_name: str = "RSS_BRIDGE_TOKEN",
        pagerduty_routing_key_secret: Optional[str] = None,
        pagerduty_source: str = "echo-bridge",
        pagerduty_component: Optional[str] = None,
        pagerduty_group: Optional[str] = None,
        opsgenie_api_key_secret: Optional[str] = None,
        opsgenie_team: Optional[str] = None,
        tcp_endpoints: Optional[Sequence[str]] = None,
        tcp_secret_name: str = "TCP_RELAY_TOKEN",
        iot_channel: Optional[str] = None,
        iot_secret_name: str = "IOT_RELAY_TOKEN",
        kafka_topic: Optional[str] = None,
        kafka_bootstrap_servers: Optional[Sequence[str]] = None,
        kafka_secret_name: str = "KAFKA_RELAY_TOKEN",
        wifi_ssid: Optional[str] = None,
        wifi_channel: Optional[str] = None,
        wifi_bandwidth_mhz: Optional[float] = None,
        wifi_frequency_mhz: Optional[float] = None,
        bluetooth_beacon_id: Optional[str] = None,
        bluetooth_profile: Optional[str] = None,
        bluetooth_bandwidth_mhz: Optional[float] = None,
        bluetooth_frequency_mhz: Optional[float] = None,
        s3_bucket: Optional[str] = None,
        s3_prefix: Optional[str] = None,
        s3_region: Optional[str] = None,
        s3_secret_name: str = "S3_RELAY_TOKEN",
        arweave_gateway_url: Optional[str] = None,
        arweave_wallet_secret_name: str = "ARWEAVE_WALLET_JWK",
    ) -> None:
        self.github_repository = github_repository
        self.github_discussions_repository = (
            github_discussions_repository.strip()
            if isinstance(github_discussions_repository, str)
            else None
        )
        self.github_discussion_category = (
            github_discussion_category or "Announcements"
        ).strip() or "Announcements"
        self.github_discussions_secret_name = github_discussions_secret_name
        self.telegram_chat_id = telegram_chat_id
        self.firebase_collection = firebase_collection
        self.slack_webhook_url = slack_webhook_url
        self.slack_channel = slack_channel
        self.slack_secret_name = slack_secret_name
        self.webhook_url = webhook_url
        self.webhook_secret_name = webhook_secret_name
        self.discord_webhook_url = discord_webhook_url
        self.discord_secret_name = discord_secret_name
        self.bluesky_identifier = bluesky_identifier
        self.bluesky_service_url = bluesky_service_url
        self.bluesky_app_password_secret = bluesky_app_password_secret
        self.mastodon_instance_url = mastodon_instance_url
        self.mastodon_visibility = (mastodon_visibility or "unlisted").strip() or "unlisted"
        self.mastodon_secret_name = mastodon_secret_name
        self.matrix_homeserver = matrix_homeserver
        self.matrix_room_id = matrix_room_id
        self.matrix_secret_name = matrix_secret_name
        self.activitypub_inbox_url = activitypub_inbox_url
        self.activitypub_actor = activitypub_actor
        self.activitypub_secret_name = activitypub_secret_name
        self.teams_webhook_url = teams_webhook_url
        self.teams_secret_name = teams_secret_name
        self.farcaster_identity = farcaster_identity
        self.farcaster_secret_name = farcaster_secret_name
        self.nostr_relays = tuple(self._normalise_links(nostr_relays)) if nostr_relays else ()
        self.nostr_public_key = nostr_public_key
        self.nostr_secret_name = nostr_secret_name
        self.sms_recipients = tuple(self._normalise_recipients(sms_recipients or []))
        self.sms_secret_name = sms_secret_name
        self.sms_from_number = sms_from_number
        self.statuspage_page_id = statuspage_page_id
        self.statuspage_secret_name = statuspage_secret_name
        self.email_recipients = tuple(self._normalise_recipients(email_recipients or []))
        self.email_secret_name = email_secret_name
        self.email_subject_template = email_subject_template
        self.notion_database_id = notion_database_id
        self.notion_secret_name = notion_secret_name
        self.dns_root_domain = dns_root_domain
        self.dns_additional_root_domains = (
            tuple(self._normalise_domains(dns_additional_root_domains))
            if dns_additional_root_domains
            else ()
        )
        self.dns_record_prefix = (dns_record_prefix or "").strip()
        self.dns_provider = dns_provider
        self.dns_secret_name = dns_secret_name
        self.dns_root_authority = (dns_root_authority or "").strip() or None
        self.dns_attestation_path = (dns_attestation_path or "").strip() or None
        self.unstoppable_domains = tuple(self._normalise_links(unstoppable_domains)) if unstoppable_domains else ()
        self.unstoppable_secret_name = unstoppable_secret_name
        self.vercel_projects = tuple(self._normalise_links(vercel_projects)) if vercel_projects else ()
        self.vercel_secret_name = vercel_secret_name
        self.linkedin_organization_id = (linkedin_organization_id or "").strip() or None
        self.linkedin_secret_name = linkedin_secret_name
        self.reddit_subreddit = (reddit_subreddit or "").strip() or None
        self.reddit_secret_name = reddit_secret_name
        self.rss_feed_url = (rss_feed_url or "").strip() or None
        self.rss_secret_name = rss_secret_name
        self.pagerduty_routing_key_secret = (
            pagerduty_routing_key_secret.strip()
            if isinstance(pagerduty_routing_key_secret, str)
            else None
        )
        self.pagerduty_source = pagerduty_source or "echo-bridge"
        self.pagerduty_component = (pagerduty_component or "").strip() or None
        self.pagerduty_group = (pagerduty_group or "").strip() or None
        self.opsgenie_api_key_secret = (
            opsgenie_api_key_secret.strip()
            if isinstance(opsgenie_api_key_secret, str)
            else None
        )
        self.opsgenie_team = (opsgenie_team or "").strip() or None
        self.tcp_endpoints = tuple(self._normalise_links(tcp_endpoints)) if tcp_endpoints else ()
        self.tcp_secret_name = tcp_secret_name
        self.iot_channel = (iot_channel or "").strip() or None
        self.iot_secret_name = iot_secret_name
        self.kafka_topic = (kafka_topic or "").strip() or None
        self.kafka_bootstrap_servers = (
            tuple(self._normalise_links(kafka_bootstrap_servers))
            if kafka_bootstrap_servers
            else ()
        )
        self.kafka_secret_name = kafka_secret_name
        self.wifi_ssid = (wifi_ssid or "").strip() or None
        self.wifi_channel = (wifi_channel or "").strip() or None
        self.wifi_bandwidth_mhz = wifi_bandwidth_mhz
        self.wifi_frequency_mhz = wifi_frequency_mhz
        self.bluetooth_beacon_id = (bluetooth_beacon_id or "").strip() or None
        self.bluetooth_profile = (bluetooth_profile or "").strip() or None
        self.bluetooth_bandwidth_mhz = bluetooth_bandwidth_mhz
        self.bluetooth_frequency_mhz = bluetooth_frequency_mhz
        self.s3_bucket = (s3_bucket or "").strip() or None
        self.s3_prefix = (s3_prefix or "").strip() or None
        self.s3_region = (s3_region or "").strip() or None
        self.s3_secret_name = s3_secret_name
        self.arweave_gateway_url = (arweave_gateway_url or "").strip() or None
        self.arweave_wallet_secret_name = arweave_wallet_secret_name

    def plan_identity_relay(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Optional[Dict[str, Any]] = None,
        summary: Optional[str] = None,
        links: Optional[Sequence[str]] = None,
        topics: Optional[Sequence[str]] = None,
        priority: Optional[str] = None,
        connectors: Optional[Sequence[str]] = None,
    ) -> List[BridgePlan]:
        """Build relay plans for configured connectors.

        When ``connectors`` are provided, only matching platform plans will be
        generated. Connector names are matched case-insensitively so callers
        can forward user-controlled filters without additional normalisation.
        """

        traits = self._normalise_traits(traits or {})
        summary_text = self._normalise_summary(summary)
        link_items = self._normalise_links(links)
        topic_items = self._normalise_topics(topics)
        priority_text = self._normalise_priority(priority)
        allowed_platforms = self._normalise_connectors(connectors)
        context = RelayContext(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits=traits,
            summary=summary_text,
            links=link_items,
            topics=topic_items,
            priority=priority_text,
        )
        plans: List[BridgePlan] = []
        context.base_document = self._base_document(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits=traits,
            summary=summary_text,
            links=link_items,
            topics=topic_items,
            priority=priority_text,
        )

        if (
            (self.dns_root_domain or self.dns_additional_root_domains)
            and self._platform_enabled("dns", allowed_platforms)
        ):
            plans.append(
                self._dns_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    topics=topic_items,
                )
            )

        if self.unstoppable_domains and self._platform_enabled("unstoppable", allowed_platforms):
            plans.append(
                self._unstoppable_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                )
            )

        if self.vercel_projects and self._platform_enabled("vercel", allowed_platforms):
            plans.append(
                self._vercel_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                )
            )

        if self.kafka_topic and self._platform_enabled("kafka", allowed_platforms):
            plans.append(
                self._kafka_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    document=context.base_document,
                )
            )

        if self.s3_bucket and self._platform_enabled("s3", allowed_platforms):
            plans.append(
                self._s3_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    document=context.base_document,
                )
            )

        if self.github_repository and self._platform_enabled("github", allowed_platforms):
            context.markdown_body = context.markdown_body or self._render_markdown(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._github_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    topics=topic_items,
                    priority=priority_text,
                    body=context.markdown_body,
                )
            )
        if (
            self.github_discussions_repository
            and self._platform_enabled("github_discussions", allowed_platforms)
        ):
            context.markdown_body = context.markdown_body or self._render_markdown(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._github_discussion_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    body=context.markdown_body,
                )
            )
        if self.telegram_chat_id and self._platform_enabled("telegram", allowed_platforms):
            context.plain_text = context.plain_text or self._render_plain(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._telegram_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    topics=topic_items,
                    priority=priority_text,
                    text=context.plain_text,
                )
            )
        if self.firebase_collection and self._platform_enabled("firebase", allowed_platforms):
            plans.append(
                self._firebase_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    document=context.base_document,
                )
            )
        if self.slack_webhook_url and self._platform_enabled("slack", allowed_platforms):
            context.plain_text = context.plain_text or self._render_plain(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._slack_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    text=context.plain_text,
                )
            )
        if self.discord_webhook_url and self._platform_enabled("discord", allowed_platforms):
            context.plain_text = context.plain_text or self._render_plain(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._discord_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    text=context.plain_text,
                )
            )
        if self.bluesky_identifier and self._platform_enabled("bluesky", allowed_platforms):
            context.social_text = context.social_text or self._render_social(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._bluesky_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    text=context.social_text,
                )
            )
        if self.mastodon_instance_url and self._platform_enabled("mastodon", allowed_platforms):
            context.social_text = context.social_text or self._render_social(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._mastodon_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    text=context.social_text,
                )
            )
        if self.activitypub_inbox_url and self._platform_enabled("activitypub", allowed_platforms):
            context.social_text = context.social_text or self._render_social(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._activitypub_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    text=context.social_text,
                )
            )
        if self.arweave_gateway_url and self._platform_enabled("arweave", allowed_platforms):
            plans.append(
                self._arweave_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                )
            )
        if self.teams_webhook_url and self._platform_enabled("teams", allowed_platforms):
            context.plain_text = context.plain_text or self._render_plain(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._teams_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    text=context.plain_text,
                )
            )
        if (
            self.matrix_homeserver
            and self.matrix_room_id
            and self._platform_enabled("matrix", allowed_platforms)
        ):
            context.social_text = context.social_text or self._render_social(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._matrix_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                topics=topic_items,
                priority=priority_text,
                text=context.social_text,
            )
        )
        if (
            self.nostr_relays
            and self.nostr_public_key
            and self._platform_enabled("nostr", allowed_platforms)
        ):
            context.social_text = context.social_text or self._render_social(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._nostr_plan(
                    identity=identity,
                    cycle=cycle,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    content=context.social_text,
                )
            )
        if self.farcaster_identity and self._platform_enabled("farcaster", allowed_platforms):
            context.social_text = context.social_text or self._render_social(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._farcaster_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    text=context.social_text,
                )
            )
        if self.sms_recipients and self._platform_enabled("sms", allowed_platforms):
            context.plain_text = context.plain_text or self._render_plain(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._sms_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    text=context.plain_text,
                )
            )
        if self.statuspage_page_id and self._platform_enabled("statuspage", allowed_platforms):
            context.plain_text = context.plain_text or self._render_plain(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._statuspage_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    text=context.plain_text,
                )
            )
        if self.email_recipients and self._platform_enabled("email", allowed_platforms):
            context.plain_text = context.plain_text or self._render_plain(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._email_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    text=context.plain_text,
                )
            )
        if self.notion_database_id and self._platform_enabled("notion", allowed_platforms):
            context.markdown_body = context.markdown_body or self._render_markdown(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._notion_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    document=context.markdown_body,
                )
            )
        if self.webhook_url and self._platform_enabled("webhook", allowed_platforms):
            plans.append(
                self._webhook_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    payload=context.base_document,
                )
            )
        if self.tcp_endpoints and self._platform_enabled("tcp", allowed_platforms):
            context.plain_text = context.plain_text or self._render_plain(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._tcp_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    text=context.plain_text,
                )
            )
        if self.iot_channel and self._platform_enabled("iot", allowed_platforms):
            plans.append(
                self._iot_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    document=context.base_document,
                )
            )
        if self.wifi_ssid and self._platform_enabled("wifi", allowed_platforms):
            context.plain_text = context.plain_text or self._render_plain(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._wifi_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    text=context.plain_text,
                )
            )
        if (
            self.bluetooth_beacon_id
            and self._platform_enabled("bluetooth", allowed_platforms)
        ):
            context.plain_text = context.plain_text or self._render_plain(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._bluetooth_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    text=context.plain_text,
                )
            )
        if self.rss_feed_url and self._platform_enabled("rss", allowed_platforms):
            context.markdown_body = context.markdown_body or self._render_markdown(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._rss_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    body=context.markdown_body,
                )
            )
        if self.pagerduty_routing_key_secret and self._platform_enabled(
            "pagerduty", allowed_platforms
        ):
            context.plain_text = context.plain_text or self._render_plain(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._pagerduty_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    text=context.plain_text,
                )
            )
        if self.linkedin_organization_id and self._platform_enabled(
            "linkedin", allowed_platforms
        ):
            context.social_text = context.social_text or self._render_social(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._linkedin_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    text=context.social_text,
                )
            )
        if self.reddit_subreddit and self._platform_enabled("reddit", allowed_platforms):
            context.social_text = context.social_text or self._render_social(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._reddit_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    text=context.social_text,
                )
            )
        if self.opsgenie_api_key_secret and self._platform_enabled(
            "opsgenie", allowed_platforms
        ):
            context.plain_text = context.plain_text or self._render_plain(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
                topics=topic_items,
                priority=priority_text,
            )
            plans.append(
                self._opsgenie_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    topics=topic_items,
                    priority=priority_text,
                    text=context.plain_text,
                    document=context.base_document,
                )
            )

        return plans

    # ------------------------------------------------------------------
    # Individual platform helpers
    # ------------------------------------------------------------------
    def _github_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        topics: Optional[List[str]] = None,
        priority: Optional[str] = None,
        body: Optional[str] = None,
    ) -> BridgePlan:
        owner, name = self.github_repository.split("/", 1)
        payload = {
            "owner": owner,
            "repo": name,
            "title": f"Echo Identity Relay :: {identity} :: Cycle {cycle}",
            "body": body
            or self._render_markdown(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=None,
                links=[],
                topics=topics or [],
                priority=priority,
            ),
            "labels": ["echo-bridge", identity.lower()],
        }
        return BridgePlan(platform="github", action="create_issue", payload=payload, requires_secret=["GITHUB_TOKEN"])

    def _github_discussion_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        body: Optional[str] = None,
    ) -> BridgePlan:
        owner, name = self.github_discussions_repository.split("/", 1)
        content = body or self._render_markdown(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits=traits,
            summary=summary,
            links=links,
            topics=topics,
            priority=priority,
        )
        payload = {
            "owner": owner,
            "repo": name,
            "category": self.github_discussion_category,
            "title": f"Echo Identity Relay :: {identity} :: Cycle {cycle}",
            "body": content,
            "context": {"identity": identity, "cycle": cycle, "signature": signature},
        }
        requires = [self.github_discussions_secret_name] if self.github_discussions_secret_name else []
        return BridgePlan(
            platform="github_discussions",
            action="create_discussion",
            payload=payload,
            requires_secret=requires,
        )

    def _telegram_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        topics: List[str],
        priority: Optional[str],
        text: Optional[str] = None,
    ) -> BridgePlan:
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": text
            or self._render_plain(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=None,
                links=[],
                topics=topics,
                priority=priority,
            ),
            "parse_mode": "MarkdownV2",
        }
        return BridgePlan(platform="telegram", action="send_message", payload=payload, requires_secret=["TELEGRAM_BOT_TOKEN"])

    def _firebase_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        document: Optional[Dict[str, Any]] = None,
    ) -> BridgePlan:
        record = document or self._base_document(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits=traits,
            summary=None,
            links=[],
            topics=[],
            priority=None,
        )
        payload = {
            "collection": self.firebase_collection,
            "document": f"echo::{identity}::{cycle}",
            "data": record,
        }
        return BridgePlan(platform="firebase", action="set_document", payload=payload, requires_secret=["FIREBASE_SERVICE_ACCOUNT"])

    def _slack_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        text: Optional[str] = None,
    ) -> BridgePlan:
        attachments: List[Dict[str, Any]] = []
        if priority:
            attachments.append({"title": "Priority", "text": priority})
        if topics:
            attachments.append({"title": "Topics", "text": ", ".join(topics)})
        if summary:
            attachments.append({"title": "Summary", "text": summary})
        attachments.extend(self._attachment_traits(traits))
        attachments.extend(self._attachment_links(links))
        payload: Dict[str, Any] = {
            "webhook_env": self.slack_secret_name,
            "text": text
            or self._render_plain(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary,
                links=links,
                topics=topics,
                priority=priority,
            ),
            "context": {"identity": identity, "cycle": cycle, "signature": signature},
        }
        if attachments:
            payload["attachments"] = attachments
        if self.slack_channel:
            payload["channel"] = self.slack_channel
        requires = [self.slack_secret_name] if self.slack_secret_name else []
        return BridgePlan(platform="slack", action="send_webhook", payload=payload, requires_secret=requires)

    def _discord_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        text: Optional[str] = None,
    ) -> BridgePlan:
        embeds: List[Dict[str, Any]] = []
        if summary or traits or links:
            embed: Dict[str, Any] = {
                "title": f"Echo Bridge :: {identity}",
                "description": summary or f"Cycle {cycle} relay",
                "fields": [
                    {"name": key, "value": str(value), "inline": True}
                    for key, value in self._sorted_traits(traits)
                ],
                "url": links[0] if links else None,
            }
            if priority:
                embed["fields"].append({"name": "Priority", "value": priority, "inline": True})
            if topics:
                embed["fields"].append({"name": "Topics", "value": ", ".join(topics), "inline": False})
            if not embed["fields"]:
                embed.pop("fields")
            if embed.get("url") is None:
                embed.pop("url")
            embeds.append(embed)
        payload: Dict[str, Any] = {
            "webhook_env": self.discord_secret_name,
            "content": text
            or self._render_plain(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary,
                links=links,
                topics=topics,
                priority=priority,
            ),
            "context": {"identity": identity, "cycle": cycle, "signature": signature},
        }
        if embeds:
            payload["embeds"] = embeds
        requires = [self.discord_secret_name] if self.discord_secret_name else []
        return BridgePlan(platform="discord", action="send_webhook", payload=payload, requires_secret=requires)

    def _bluesky_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        text: Optional[str] = None,
    ) -> BridgePlan:
        status = text or self._render_social(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits=traits,
            summary=summary,
            links=links,
            topics=topics,
            priority=priority,
        )
        payload: Dict[str, Any] = {
            "service": self.bluesky_service_url,
            "identifier": self.bluesky_identifier,
            "text": status,
            "context": {"identity": identity, "cycle": cycle, "signature": signature},
        }
        if links:
            payload["links"] = links[:2]
        if topics:
            payload["tags"] = [self._topic_hashtag(topic) for topic in topics]
        requires = [self.bluesky_app_password_secret] if self.bluesky_app_password_secret else []
        return BridgePlan(platform="bluesky", action="post_record", payload=payload, requires_secret=requires)

    def _mastodon_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        text: Optional[str] = None,
    ) -> BridgePlan:
        status = text or self._render_social(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits=traits,
            summary=summary,
            links=links,
            topics=topics,
            priority=priority,
        )
        payload: Dict[str, Any] = {
            "instance": self.mastodon_instance_url,
            "status": status,
            "visibility": self.mastodon_visibility,
            "context": {"identity": identity, "cycle": cycle, "signature": signature},
        }
        if links:
            payload["links"] = links[:2]
        if topics:
            payload["tags"] = topics
        if priority:
            payload["priority"] = priority
        requires = [self.mastodon_secret_name] if self.mastodon_secret_name else []
        return BridgePlan(platform="mastodon", action="post_status", payload=payload, requires_secret=requires)

    def _activitypub_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        text: Optional[str] = None,
    ) -> BridgePlan:
        status = text or self._render_social(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits=traits,
            summary=summary,
            links=links,
            topics=topics,
            priority=priority,
        )
        payload: Dict[str, Any] = {
            "actor": self.activitypub_actor,
            "inbox": self.activitypub_inbox_url,
            "status": status,
            "context": {"identity": identity, "cycle": cycle, "signature": signature},
        }
        if links:
            payload["links"] = links[:2]
        if topics:
            payload["tags"] = [self._topic_hashtag(topic) for topic in topics]
        if priority:
            payload["priority"] = priority
        requires = [self.activitypub_secret_name] if self.activitypub_secret_name else []
        return BridgePlan(platform="activitypub", action="deliver_note", payload=payload, requires_secret=requires)

    def _matrix_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        text: Optional[str] = None,
    ) -> BridgePlan:
        message = text or self._render_social(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits=traits,
            summary=summary,
            links=links,
            topics=topics,
            priority=priority,
        )
        payload: Dict[str, Any] = {
            "homeserver": self.matrix_homeserver,
            "room_id": self.matrix_room_id,
            "text": message,
            "context": {"identity": identity, "cycle": cycle, "signature": signature},
        }
        if links:
            payload["links"] = links
        if topics:
            payload["topics"] = topics
        if priority:
            payload["priority"] = priority
        requires = [self.matrix_secret_name] if self.matrix_secret_name else []
        return BridgePlan(platform="matrix", action="send_room_message", payload=payload, requires_secret=requires)

    def _teams_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        text: Optional[str] = None,
    ) -> BridgePlan:
        payload: Dict[str, Any] = {
            "webhook_env": self.teams_secret_name,
            "context": {"identity": identity, "cycle": cycle, "signature": signature},
            "text": text
            or self._render_plain(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary,
                links=links,
                topics=topics,
                priority=priority,
            ),
        }
        if summary:
            payload["summary"] = summary
        if links:
            payload["links"] = links
        if topics:
            payload["topics"] = topics
        if priority:
            payload["priority"] = priority
        requires = [self.teams_secret_name] if self.teams_secret_name else []
        return BridgePlan(platform="teams", action="send_webhook", payload=payload, requires_secret=requires)

    def _farcaster_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        text: Optional[str] = None,
    ) -> BridgePlan:
        payload: Dict[str, Any] = {
            "identity": self.farcaster_identity,
            "text": text
            or self._render_social(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary,
                links=links,
                topics=topics,
                priority=priority,
            ),
            "context": {"identity": identity, "cycle": cycle, "signature": signature},
        }
        if links:
            payload["attachments"] = links[:2]
        if topics:
            payload["tags"] = topics
        if priority:
            payload["priority"] = priority
        requires = [self.farcaster_secret_name] if self.farcaster_secret_name else []
        return BridgePlan(platform="farcaster", action="post_cast", payload=payload, requires_secret=requires)

    def _nostr_plan(
        self,
        *,
        identity: str,
        cycle: str,
        summary: Optional[str],
        links: Sequence[str],
        topics: Sequence[str],
        priority: Optional[str],
        content: str,
    ) -> BridgePlan:
        tags: List[List[str]] = []
        if summary:
            tags.append(["subject", summary])
        if priority:
            tags.append(["priority", priority])
        for link in links:
            tags.append(["r", link])
        for topic in topics:
            slug = self._topic_hashtag(topic)
            if slug:
                tags.append(["t", slug])
        payload = {
            "relays": list(self.nostr_relays),
            "pubkey": self.nostr_public_key,
            "content": content,
            "tags": tags,
            "context": {
                "identity": identity,
                "cycle": cycle,
            },
        }
        requires = [self.nostr_secret_name] if self.nostr_secret_name else []
        return BridgePlan(
            platform="nostr",
            action="post_event",
            payload=payload,
            requires_secret=requires,
        )

    def _linkedin_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        text: Optional[str] = None,
    ) -> BridgePlan:
        share_text = text or self._render_social(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits=traits,
            summary=summary,
            links=links,
            topics=topics,
            priority=priority,
        )
        payload: Dict[str, Any] = {
            "organization_id": self.linkedin_organization_id,
            "text": share_text,
            "context": {"identity": identity, "cycle": cycle, "signature": signature},
        }
        if links:
            payload["links"] = links[:3]
        if topics:
            payload["tags"] = [self._topic_hashtag(topic) for topic in topics]
        if priority:
            payload["priority"] = priority
        if traits:
            payload["traits"] = traits
        requires = [self.linkedin_secret_name] if self.linkedin_secret_name else []
        return BridgePlan(
            platform="linkedin",
            action="create_share",
            payload=payload,
            requires_secret=requires,
        )

    def _reddit_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        text: Optional[str] = None,
    ) -> BridgePlan:
        post_text = text or self._render_social(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits=traits,
            summary=summary,
            links=links,
            topics=topics,
            priority=priority,
        )
        payload: Dict[str, Any] = {
            "subreddit": self.reddit_subreddit,
            "title": f"Echo Relay {identity}/{cycle}",
            "text": post_text,
            "context": {"identity": identity, "cycle": cycle, "signature": signature},
        }
        if links:
            payload["links"] = links
        if topics:
            payload["topics"] = topics
        if priority:
            payload["priority"] = priority
        if summary:
            payload["summary"] = summary
        requires = [self.reddit_secret_name] if self.reddit_secret_name else []
        return BridgePlan(
            platform="reddit",
            action="submit_post",
            payload=payload,
            requires_secret=requires,
        )

    def _email_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        text: Optional[str] = None,
    ) -> BridgePlan:
        subject = self._render_email_subject(identity=identity, cycle=cycle)
        body = text or self._render_plain(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits=traits,
            summary=summary,
            links=links,
            topics=topics,
            priority=priority,
        )
        payload: Dict[str, Any] = {
            "recipients": list(self.email_recipients),
            "subject": subject,
            "body": body,
            "context": {"identity": identity, "cycle": cycle, "signature": signature},
            "links": links,
        }
        if topics:
            payload["topics"] = topics
        if priority:
            payload["priority"] = priority
        requires = [self.email_secret_name] if self.email_secret_name else []
        return BridgePlan(platform="email", action="send_email", payload=payload, requires_secret=requires)

    def _notion_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        document: str,
    ) -> BridgePlan:
        title = f"Echo Bridge :: {identity} :: Cycle {cycle}"
        properties: Dict[str, Any] = {
            "Name": {"title": [{"text": {"content": title}}]},
            "Identity": {"rich_text": [{"text": {"content": identity}}]},
            "Cycle": {"rich_text": [{"text": {"content": cycle}}]},
            "Signature": {"rich_text": [{"text": {"content": signature}}]},
        }
        if traits:
            trait_text = ", ".join(f"{key}={value}" for key, value in self._sorted_traits(traits))
            if trait_text:
                properties["Traits"] = {"rich_text": [{"text": {"content": trait_text}}]}
        if summary:
            properties["Summary"] = {"rich_text": [{"text": {"content": summary}}]}
        if topics:
            properties["Topics"] = {"multi_select": [{"name": topic} for topic in topics]}
        if priority:
            properties["Priority"] = {"select": {"name": priority}}

        children: List[Dict[str, Any]] = []
        if summary:
            children.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": summary}}]},
                }
            )
        if links:
            for link in links:
                children.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {"type": "text", "text": {"content": link}},
                            ]
                        },
                    }
                )
        if document:
            children.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": document}}]},
                }
            )

        payload: Dict[str, Any] = {
            "database_id": self.notion_database_id,
            "properties": properties,
            "children": children,
            "context": {
                "identity": identity,
                "cycle": cycle,
                "signature": signature,
                "topics": topics,
                "priority": priority,
                "links": links,
            },
        }
        requires = [self.notion_secret_name] if self.notion_secret_name else []
        return BridgePlan(platform="notion", action="create_page", payload=payload, requires_secret=requires)

    def _webhook_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> BridgePlan:
        record = payload or self._base_document(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits={},
            summary=None,
            links=[],
            topics=[],
            priority=None,
        )
        body = {
            "url_hint": self.webhook_url,
            "json": record,
        }
        requires = [self.webhook_secret_name] if self.webhook_secret_name else []
        return BridgePlan(platform="webhook", action="post_json", payload=body, requires_secret=requires)

    def _arweave_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
    ) -> BridgePlan:
        document = self._base_document(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits=traits,
            summary=summary,
            links=links,
            topics=topics,
            priority=priority,
        )
        tags: List[Dict[str, str]] = [
            {"name": "App-Name", "value": "EchoBridge"},
            {"name": "App-Version", "value": "1.0"},
            {"name": "Content-Type", "value": "application/json"},
            {"name": "Identity", "value": identity},
            {"name": "Cycle", "value": cycle},
        ]
        for topic in topics[:3]:
            tags.append({"name": "Topic", "value": topic})

        payload: Dict[str, Any] = {
            "gateway_url": self.arweave_gateway_url or "https://arweave.net",
            "transaction": {
                "data": document,
                "content_type": "application/json",
                "tags": tags,
            },
            "context": {"identity": identity, "cycle": cycle, "signature": signature},
        }
        requires = (
            [self.arweave_wallet_secret_name]
            if self.arweave_wallet_secret_name
            else []
        )
        return BridgePlan(
            platform="arweave",
            action="submit_transaction",
            payload=payload,
            requires_secret=requires,
        )

    def _wifi_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        text: str,
    ) -> BridgePlan:
        context = self._base_document(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits=traits,
            summary=summary,
            links=links,
            topics=topics,
            priority=priority,
        )
        transport = {
            "band": "wifi",
            "ssid": self.wifi_ssid,
            "channel": self.wifi_channel or "auto",
            "bandwidth_mhz": round(self.wifi_bandwidth_mhz, 2)
            if isinstance(self.wifi_bandwidth_mhz, (int, float))
            else 20.0,
            "frequency_mhz": self._resolve_wifi_frequency(),
        }
        payload: Dict[str, Any] = {
            "transport": {key: value for key, value in transport.items() if value is not None},
            "message": text,
            "context": context,
        }
        return BridgePlan(
            platform="wifi",
            action="broadcast_frame",
            payload=payload,
            requires_secret=[],
        )

    def _bluetooth_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        text: str,
    ) -> BridgePlan:
        context = self._base_document(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits=traits,
            summary=summary,
            links=links,
            topics=topics,
            priority=priority,
        )
        transport = {
            "band": "bluetooth",
            "beacon_id": self.bluetooth_beacon_id,
            "profile": self.bluetooth_profile or "GATT",
            "bandwidth_mhz": round(self.bluetooth_bandwidth_mhz, 2)
            if isinstance(self.bluetooth_bandwidth_mhz, (int, float))
            else 2.0,
            "frequency_mhz": self._resolve_bluetooth_frequency(),
        }
        payload: Dict[str, Any] = {
            "transport": {key: value for key, value in transport.items() if value is not None},
            "message": text,
            "context": context,
        }
        return BridgePlan(
            platform="bluetooth",
            action="emit_beacon",
            payload=payload,
            requires_secret=[],
        )

    def _resolve_wifi_frequency(self) -> float | None:
        if isinstance(self.wifi_frequency_mhz, (int, float)):
            return float(self.wifi_frequency_mhz)

        if not self.wifi_channel:
            return None

        try:
            channel = int(str(self.wifi_channel).strip())
        except ValueError:
            return None

        if channel == 14:
            return 2484.0
        if 1 <= channel <= 13:
            return 2407.0 + 5 * channel
        if 36 <= channel <= 165:
            return 5000.0 + 5 * channel
        return None

    def _resolve_bluetooth_frequency(self) -> float:
        if isinstance(self.bluetooth_frequency_mhz, (int, float)):
            return float(self.bluetooth_frequency_mhz)
        return 2402.0

    def _rss_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        body: Optional[str] = None,
    ) -> BridgePlan:
        title = f"Echo Relay {identity}/{cycle}"
        entry: Dict[str, Any] = {
            "title": title,
            "signature": signature,
            "identity": identity,
            "cycle": cycle,
        }
        if summary:
            entry["summary"] = summary
        if links:
            entry["links"] = links
        if topics:
            entry["topics"] = topics
        if priority:
            entry["priority"] = priority
        if body:
            entry["content"] = body
        payload = {
            "feed_url": self.rss_feed_url,
            "entry": entry,
            "context": {"identity": identity, "cycle": cycle, "signature": signature},
        }
        requires = [self.rss_secret_name] if self.rss_secret_name else []
        return BridgePlan(platform="rss", action="publish_entry", payload=payload, requires_secret=requires)

    def _pagerduty_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        text: str,
    ) -> BridgePlan:
        payload = {
            "routing_key_env": self.pagerduty_routing_key_secret,
            "event_action": "trigger",
            "dedup_key": f"{identity}:{cycle}",
            "payload": {
                "summary": summary or f"Echo Bridge Relay {identity}/{cycle}",
                "source": self.pagerduty_source,
                "severity": self._pagerduty_severity(priority),
                "class": "EchoBridgeRelay",
                "component": self.pagerduty_component,
                "group": self.pagerduty_group,
                "custom_details": {
                    "identity": identity,
                    "cycle": cycle,
                    "signature": signature,
                    "traits": traits,
                    "topics": topics,
                    "links": links,
                    "priority": priority,
                    "summary": summary,
                    "rendered": text,
                },
            },
        }

        payload["payload"] = {
            key: value for key, value in payload["payload"].items() if value is not None
        }
        return BridgePlan(
            platform="pagerduty",
            action="trigger_event",
            payload=payload,
            requires_secret=[self.pagerduty_routing_key_secret]
            if self.pagerduty_routing_key_secret
            else [],
        )

    def _opsgenie_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        text: str,
        document: Dict[str, Any],
    ) -> BridgePlan:
        tags = [self._topic_hashtag(topic) or topic for topic in topics]
        tags.append("EchoBridge")

        payload: Dict[str, Any] = {
            "api_key_env": self.opsgenie_api_key_secret,
            "message": summary or f"Echo Bridge Relay {identity}/{cycle}",
            "alias": f"echo-bridge-{identity}-{cycle}",
            "description": text,
            "priority": self._opsgenie_priority(priority),
            "tags": tags,
            "details": document,
        }
        if self.opsgenie_team:
            payload["responders"] = [
                {"type": "team", "name": self.opsgenie_team, "identifierType": "name"}
            ]

        return BridgePlan(
            platform="opsgenie",
            action="create_alert",
            payload=payload,
            requires_secret=[self.opsgenie_api_key_secret]
            if self.opsgenie_api_key_secret
            else [],
        )

    def _tcp_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        text: str,
    ) -> BridgePlan:
        context = self._base_document(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits=traits,
            summary=summary,
            links=links,
            topics=topics,
            priority=priority,
        )
        payload = {
            "endpoints": list(self.tcp_endpoints),
            "body": text,
            "context": context,
        }
        requires = [self.tcp_secret_name] if self.tcp_secret_name else []
        return BridgePlan(platform="tcp", action="send_payload", payload=payload, requires_secret=requires)

    def _iot_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        document: Dict[str, Any],
    ) -> BridgePlan:
        payload: Dict[str, Any] = {
            "channel": self.iot_channel,
            "payload": document,
            "context": {
                "identity": identity,
                "cycle": cycle,
                "signature": signature,
                "topics": topics,
                "priority": priority,
            },
        }
        requires = [self.iot_secret_name] if self.iot_secret_name else []
        return BridgePlan(platform="iot", action="publish", payload=payload, requires_secret=requires)

    def _sms_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        text: str,
    ) -> BridgePlan:
        payload: Dict[str, Any] = {
            "recipients": list(self.sms_recipients),
            "body": text,
            "context": {"identity": identity, "cycle": cycle, "signature": signature},
        }
        if self.sms_from_number:
            payload["from_number"] = self.sms_from_number
        if topics:
            payload["topics"] = topics
        if priority:
            payload["priority"] = priority
        if links:
            payload["links"] = links[:2]
        requires = [self.sms_secret_name] if self.sms_secret_name else []
        return BridgePlan(platform="sms", action="send_sms", payload=payload, requires_secret=requires)

    def _statuspage_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        text: str,
    ) -> BridgePlan:
        impact = self._statuspage_impact(priority)
        incident: Dict[str, Any] = {
            "name": f"Echo Relay {identity}/{cycle}",
            "status": "investigating" if priority else "monitoring",
            "impact_override": impact,
            "body": text,
            "metadata": {
                "identity": identity,
                "cycle": cycle,
                "signature": signature,
                "traits": traits,
                "topics": topics,
            },
        }
        if summary:
            incident["summary"] = summary
        if links:
            incident["links"] = links
        payload = {"page_id": self.statuspage_page_id, "incident": incident}
        requires = [self.statuspage_secret_name] if self.statuspage_secret_name else []
        return BridgePlan(
            platform="statuspage",
            action="create_incident",
            payload=payload,
            requires_secret=requires,
        )

    def _dns_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        topics: List[str],
    ) -> BridgePlan:
        primary_domain = self.dns_root_domain or (
            self.dns_additional_root_domains[0] if self.dns_additional_root_domains else None
        )
        if not primary_domain:
            raise ValueError("At least one DNS root domain must be configured for planning")

        domains: List[str] = [primary_domain]
        for domain in self.dns_additional_root_domains:
            if domain.casefold() not in {item.casefold() for item in domains}:
                domains.append(domain)

        authority_block: Dict[str, Any] = {}
        root_authority = self.dns_root_authority or primary_domain
        if root_authority:
            authority_block["root"] = root_authority
        if self.dns_provider:
            authority_block["provider"] = self.dns_provider
        if self.dns_attestation_path:
            authority_block["attestation"] = self.dns_attestation_path
        if self.dns_record_prefix:
            authority_block["record_prefix"] = self.dns_record_prefix

        records: List[Dict[str, Any]] = []
        for domain in domains:
            record_name = domain
            if self.dns_record_prefix:
                record_name = (
                    f"{self.dns_record_prefix}.{domain}" if domain else self.dns_record_prefix
                )
            records.append(
                {
                    "provider": self.dns_provider,
                    "root_domain": domain,
                    "record": record_name,
                    "type": "TXT",
                    "value": f"echo-root={identity}:{cycle}:{signature}",
                    "authority": authority_block,
                    "context": {
                        "identity": identity,
                        "cycle": cycle,
                        "signature": signature,
                        "traits": traits,
                        "topics": topics,
                    },
                }
            )

        payload: Dict[str, Any] = dict(records[0])
        if len(records) > 1:
            payload["records"] = records

        requires = [self.dns_secret_name] if self.dns_secret_name else []
        return BridgePlan(
            platform="dns",
            action="upsert_txt_record",
            payload=payload,
            requires_secret=requires,
        )

    def _unstoppable_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
    ) -> BridgePlan:
        records = {
            "echo.identity": identity,
            "echo.cycle": cycle,
            "echo.signature": signature,
            "echo.traits": traits,
        }
        if summary:
            records["echo.summary"] = summary
        if links:
            records["echo.links"] = links
        if topics:
            records["echo.topics"] = topics
        if priority:
            records["echo.priority"] = priority

        payload = {
            "domains": list(self.unstoppable_domains),
            "records": records,
        }

        return BridgePlan(
            platform="unstoppable",
            action="update_domain_records",
            payload=payload,
            requires_secret=[self.unstoppable_secret_name] if self.unstoppable_secret_name else [],
        )

    def _vercel_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
    ) -> BridgePlan:
        context = {
            "identity": identity,
            "cycle": cycle,
            "signature": signature,
        }
        if summary:
            context["summary"] = summary
        if links:
            context["links"] = links
        if topics:
            context["topics"] = topics
        if priority:
            context["priority"] = priority

        payload = {
            "projects": list(self.vercel_projects),
            "context": context,
        }

        return BridgePlan(
            platform="vercel",
            action="trigger_deploy",
            payload=payload,
            requires_secret=[self.vercel_secret_name] if self.vercel_secret_name else [],
        )

    def _kafka_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        document: Optional[Dict[str, Any]] = None,
    ) -> BridgePlan:
        message = document or self._base_document(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits=traits,
            summary=summary,
            links=links,
            topics=topics,
            priority=priority,
        )

        payload = {
            "topic": self.kafka_topic,
            "bootstrap_servers": list(self.kafka_bootstrap_servers),
            "message": message,
            "key": f"{identity}:{cycle}",
            "context": {
                "identity": identity,
                "cycle": cycle,
                "priority": priority,
                "topics": topics,
            },
        }

        requires = [self.kafka_secret_name] if self.kafka_secret_name else []
        return BridgePlan(
            platform="kafka",
            action="publish_event",
            payload=payload,
            requires_secret=requires,
        )

    def _s3_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
        document: Optional[Dict[str, Any]] = None,
    ) -> BridgePlan:
        record = document or self._base_document(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits=traits,
            summary=summary,
            links=links,
            topics=topics,
            priority=priority,
        )

        prefix = self.s3_prefix.strip("/") if self.s3_prefix else "bridge"
        key = f"{prefix}/{self._slugify(identity)}-{self._slugify(cycle)}.json"

        payload = {
            "bucket": self.s3_bucket,
            "key": key,
            "region": self.s3_region,
            "content_type": "application/json",
            "body": record,
            "metadata": {
                "identity": identity,
                "cycle": str(cycle),
                "priority": priority,
                "topics": topics,
            },
        }

        requires = [self.s3_secret_name] if self.s3_secret_name else []
        return BridgePlan(
            platform="s3",
            action="write_object",
            payload=payload,
            requires_secret=requires,
        )

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _base_document(
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
    ) -> Dict[str, Any]:
        document: Dict[str, Any] = {
            "identity": identity,
            "cycle": cycle,
            "signature": signature,
            "traits": traits,
        }
        if priority:
            document["priority"] = priority
        if summary:
            document["summary"] = summary
        if links:
            document["links"] = links
        if topics:
            document["topics"] = topics
        return document

    @staticmethod
    def _slugify(value: str) -> str:
        """Return a filesystem-friendly slug for connector payloads."""

        text = str(value or "").strip().casefold()
        text = re.sub(r"[^a-z0-9._-]+", "-", text)
        return text.strip("-") or "echo"

    def _normalise_traits(self, traits: Dict[str, Any]) -> Dict[str, Any]:
        normalised: Dict[str, Any] = {}
        for key, value in traits.items():
            if key is None:
                continue
            text = str(key).strip()
            if not text:
                continue
            normalised[text] = value
        return normalised

    @staticmethod
    def _normalise_summary(summary: Optional[str]) -> Optional[str]:
        if summary is None:
            return None
        text = str(summary).strip()
        return text or None

    def _normalise_links(self, links: Optional[Sequence[str]]) -> List[str]:
        if not links:
            return []
        seen = set()
        cleaned: List[str] = []
        for link in links:
            if link is None:
                continue
            text = str(link).strip()
            if not text or text in seen:
                continue
            cleaned.append(text)
            seen.add(text)
        return cleaned

    def _normalise_topics(self, topics: Optional[Sequence[str]]) -> List[str]:
        if not topics:
            return []
        seen = set()
        cleaned: List[str] = []
        for topic in topics:
            if topic is None:
                continue
            text = str(topic).strip()
            if not text:
                continue
            key = text.casefold()
            if key in seen:
                continue
            cleaned.append(text)
            seen.add(key)
        return cleaned

    def _normalise_domains(self, domains: Optional[Sequence[str]]) -> List[str]:
        if not domains:
            return []
        seen = set()
        cleaned: List[str] = []
        for domain in domains:
            if domain is None:
                continue
            text = str(domain).strip()
            if not text:
                continue
            key = text.casefold()
            if key in seen:
                continue
            cleaned.append(text)
            seen.add(key)
        return cleaned

    def _normalise_connectors(self, connectors: Optional[Sequence[str]]) -> Optional[Set[str]]:
        if not connectors:
            return None
        cleaned = {str(connector).strip().casefold() for connector in connectors if connector}
        return cleaned or None

    @staticmethod
    def _normalise_priority(priority: Optional[str]) -> Optional[str]:
        if priority is None:
            return None
        text = str(priority).strip()
        return text or None

    @staticmethod
    def _platform_enabled(platform: str, allowed: Optional[Set[str]]) -> bool:
        if allowed is None:
            return True
        return platform.casefold() in allowed

    @staticmethod
    def _topic_hashtag(topic: str) -> str:
        slug = "".join(char for char in topic if char.isalnum() or char in {"-", "_", " ", "/"}).strip()
        slug = slug.replace("/", "-").replace(" ", "")
        return slug

    def _sorted_traits(self, traits: Dict[str, Any]) -> List[Tuple[str, Any]]:
        return sorted(((key, traits[key]) for key in traits), key=lambda item: item[0].casefold())

    def _render_markdown(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
    ) -> str:
        lines = [
            f"## Echo Bridge Relay",
            "",
            f"- **Identity:** `{identity}`",
            f"- **Cycle:** `{cycle}`",
            f"- **Signature:** `{signature}`",
        ]
        if priority:
            lines.append(f"- **Priority:** `{priority}`")
        if traits:
            lines.append("- **Traits:**")
            for key, value in self._sorted_traits(traits):
                lines.append(f"  - `{key}` :: `{value}`")
        if topics:
            lines.append("- **Topics:**")
            lines.append("  - " + ", ".join(topics))
        if summary:
            lines.append("")
            lines.append("### Summary")
            lines.append(summary)
        if links:
            lines.append("")
            lines.append("### Links")
            for link in links:
                lines.append(f"- {link}")
        lines.append("")
        lines.append("_This issue was planned by EchoBridge for multi-platform coherence._")
        return "\n".join(lines)

    def _render_plain(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
    ) -> str:
        lines = [
            f"Echo Bridge Relay", f"Identity: {identity}", f"Cycle: {cycle}", f"Signature: {signature}",
        ]
        if priority:
            lines.append(f"Priority: {priority}")
        if traits:
            lines.append("Traits:")
            for key, value in self._sorted_traits(traits):
                lines.append(f" - {key}: {value}")
        if topics:
            lines.append("Topics:")
            lines.append(" - " + ", ".join(topics))
        if summary:
            lines.append("")
            lines.append(f"Summary: {summary}")
        if links:
            lines.append("Links:")
            for link in links:
                lines.append(f" - {link}")
        lines.append("\n#EchoBridge :: Sovereign ping")
        return "\n".join(lines)

    def _render_social(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        topics: List[str],
        priority: Optional[str],
    ) -> str:
        fragments: List[str] = [f"Echo Bridge :: {identity}", f"Cycle {cycle}", f"sig {signature}"]
        if summary:
            fragments.append(summary)
        if traits:
            trait_text = ", ".join(f"{key}={value}" for key, value in self._sorted_traits(traits))
            if trait_text:
                fragments.append(trait_text)
        if priority:
            fragments.append(f"priority={priority}")
        if links:
            fragments.append(" ".join(links[:2]))
        if topics:
            hashtags: List[str] = []
            for topic in topics:
                slug = self._topic_hashtag(topic)
                if slug:
                    hashtags.append(f"#{slug}")
            if hashtags:
                fragments.append(" ".join(hashtags))
        fragments.append("#EchoBridge")
        return " | ".join(fragment for fragment in fragments if fragment)

    @staticmethod
    def _statuspage_impact(priority: Optional[str]) -> str:
        if not priority:
            return "none"
        mapping = {
            "critical": "critical",
            "high": "major",
            "medium": "minor",
            "info": "none",
            "low": "none",
        }
        return mapping.get(priority.casefold(), "none")

    @staticmethod
    def _pagerduty_severity(priority: Optional[str]) -> str:
        if not priority:
            return "info"
        mapping = {
            "critical": "critical",
            "high": "error",
            "medium": "warning",
            "low": "info",
        }
        return mapping.get(priority.casefold(), "info")

    @staticmethod
    def _opsgenie_priority(priority: Optional[str]) -> str:
        if not priority:
            return "P3"
        mapping = {
            "critical": "P1",
            "high": "P2",
            "medium": "P3",
            "low": "P4",
        }
        return mapping.get(priority.casefold(), "P3")

    def _attachment_traits(self, traits: Dict[str, Any]) -> List[Dict[str, Any]]:
        attachments: List[Dict[str, Any]] = []
        for key, value in self._sorted_traits(traits):
            attachments.append({"title": key, "text": str(value)})
        return attachments

    @staticmethod
    def _attachment_links(links: List[str]) -> List[Dict[str, Any]]:
        attachments: List[Dict[str, Any]] = []
        for index, link in enumerate(links, start=1):
            attachments.append({"title": f"Link {index}", "text": link})
        return attachments

    def _normalise_recipients(self, recipients: Sequence[str]) -> List[str]:
        return self._normalise_links(recipients)

    def _render_email_subject(self, *, identity: str, cycle: str) -> str:
        template = self.email_subject_template or "Echo Identity Relay :: {identity} :: Cycle {cycle}"
        try:
            return template.format(identity=identity, cycle=cycle)
        except (IndexError, KeyError):
            return f"Echo Identity Relay :: {identity} :: Cycle {cycle}"
