"""Cross-network identity relay planning for Echo."""

from __future__ import annotations

from dataclasses import dataclass, field
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
    ) -> None:
        self.github_repository = github_repository
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
            "parent": {"database_id": self.notion_database_id},
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
