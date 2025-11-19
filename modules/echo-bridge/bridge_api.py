"""Cross-network identity relay planning for Echo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass
class BridgePlan:
    """Declarative instruction describing how to mirror identity state."""

    platform: str
    action: str
    payload: Dict[str, Any]
    requires_secret: List[str] = field(default_factory=list)


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
        mastodon_instance_url: Optional[str] = None,
        mastodon_visibility: str = "unlisted",
        mastodon_secret_name: str = "MASTODON_ACCESS_TOKEN",
        matrix_homeserver: Optional[str] = None,
        matrix_room_id: Optional[str] = None,
        matrix_secret_name: str = "MATRIX_ACCESS_TOKEN",
        email_recipients: Optional[Sequence[str]] = None,
        email_secret_name: Optional[str] = "EMAIL_RELAY_API_KEY",
        email_subject_template: str = "Echo Identity Relay :: {identity} :: Cycle {cycle}",
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
        self.mastodon_instance_url = mastodon_instance_url
        self.mastodon_visibility = (mastodon_visibility or "unlisted").strip() or "unlisted"
        self.mastodon_secret_name = mastodon_secret_name
        self.matrix_homeserver = matrix_homeserver
        self.matrix_room_id = matrix_room_id
        self.matrix_secret_name = matrix_secret_name
        self.email_recipients = tuple(self._normalise_recipients(email_recipients or []))
        self.email_secret_name = email_secret_name
        self.email_subject_template = email_subject_template

    def plan_identity_relay(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Optional[Dict[str, Any]] = None,
        summary: Optional[str] = None,
        links: Optional[Sequence[str]] = None,
    ) -> List[BridgePlan]:
        """Build relay plans for GitHub, Telegram, and Firebase."""

        traits = self._normalise_traits(traits or {})
        summary_text = self._normalise_summary(summary)
        link_items = self._normalise_links(links)
        plans: List[BridgePlan] = []
        markdown_body = None
        plain_text = None
        social_text = None
        base_document = self._base_document(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits=traits,
            summary=summary_text,
            links=link_items,
        )

        if self.github_repository:
            markdown_body = markdown_body or self._render_markdown(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
            )
            plans.append(
                self._github_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    body=markdown_body,
                )
            )
        if self.telegram_chat_id:
            plain_text = plain_text or self._render_plain(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
            )
            plans.append(
                self._telegram_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    text=plain_text,
                )
            )
        if self.firebase_collection:
            plans.append(
                self._firebase_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    document=base_document,
                )
            )
        if self.slack_webhook_url:
            plain_text = plain_text or self._render_plain(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
            )
            plans.append(
                self._slack_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    text=plain_text,
                )
            )
        if self.discord_webhook_url:
            plain_text = plain_text or self._render_plain(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
            )
            plans.append(
                self._discord_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    text=plain_text,
                )
            )
        if self.mastodon_instance_url:
            social_text = social_text or self._render_social(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
            )
            plans.append(
                self._mastodon_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    text=social_text,
                )
            )
        if self.matrix_homeserver and self.matrix_room_id:
            social_text = social_text or self._render_social(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
            )
            plans.append(
                self._matrix_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    text=social_text,
                )
            )
        if self.email_recipients:
            plain_text = plain_text or self._render_plain(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=traits,
                summary=summary_text,
                links=link_items,
            )
            plans.append(
                self._email_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    traits=traits,
                    summary=summary_text,
                    links=link_items,
                    text=plain_text,
                )
            )
        if self.webhook_url:
            plans.append(
                self._webhook_plan(
                    identity=identity,
                    cycle=cycle,
                    signature=signature,
                    payload=base_document,
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
        body: Optional[str] = None,
    ) -> BridgePlan:
        owner, name = self.github_repository.split("/", 1)
        payload = {
            "owner": owner,
            "repo": name,
            "title": f"Echo Identity Relay :: {identity} :: Cycle {cycle}",
            "body": body or self._render_markdown(identity=identity, cycle=cycle, signature=signature, traits=traits),
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
        text: Optional[str] = None,
    ) -> BridgePlan:
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": text or self._render_plain(identity=identity, cycle=cycle, signature=signature, traits=traits),
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
        text: Optional[str] = None,
    ) -> BridgePlan:
        attachments: List[Dict[str, Any]] = []
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
            ),
            "context": {"identity": identity, "cycle": cycle, "signature": signature},
        }
        if embeds:
            payload["embeds"] = embeds
        requires = [self.discord_secret_name] if self.discord_secret_name else []
        return BridgePlan(platform="discord", action="send_webhook", payload=payload, requires_secret=requires)

    def _mastodon_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        text: Optional[str] = None,
    ) -> BridgePlan:
        status = text or self._render_social(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits=traits,
            summary=summary,
            links=links,
        )
        payload: Dict[str, Any] = {
            "instance": self.mastodon_instance_url,
            "status": status,
            "visibility": self.mastodon_visibility,
            "context": {"identity": identity, "cycle": cycle, "signature": signature},
        }
        if links:
            payload["links"] = links[:2]
        requires = [self.mastodon_secret_name] if self.mastodon_secret_name else []
        return BridgePlan(platform="mastodon", action="post_status", payload=payload, requires_secret=requires)

    def _matrix_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
        text: Optional[str] = None,
    ) -> BridgePlan:
        message = text or self._render_social(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits=traits,
            summary=summary,
            links=links,
        )
        payload: Dict[str, Any] = {
            "homeserver": self.matrix_homeserver,
            "room_id": self.matrix_room_id,
            "text": message,
            "context": {"identity": identity, "cycle": cycle, "signature": signature},
        }
        if links:
            payload["links"] = links
        requires = [self.matrix_secret_name] if self.matrix_secret_name else []
        return BridgePlan(platform="matrix", action="send_room_message", payload=payload, requires_secret=requires)

    def _email_plan(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Dict[str, Any],
        summary: Optional[str],
        links: List[str],
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
        )
        payload: Dict[str, Any] = {
            "recipients": list(self.email_recipients),
            "subject": subject,
            "body": body,
            "context": {"identity": identity, "cycle": cycle, "signature": signature},
            "links": links,
        }
        requires = [self.email_secret_name] if self.email_secret_name else []
        return BridgePlan(platform="email", action="send_email", payload=payload, requires_secret=requires)

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
        )
        body = {
            "url_hint": self.webhook_url,
            "json": record,
        }
        requires = [self.webhook_secret_name] if self.webhook_secret_name else []
        return BridgePlan(platform="webhook", action="post_json", payload=body, requires_secret=requires)

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
    ) -> Dict[str, Any]:
        document: Dict[str, Any] = {
            "identity": identity,
            "cycle": cycle,
            "signature": signature,
            "traits": traits,
        }
        if summary:
            document["summary"] = summary
        if links:
            document["links"] = links
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
    ) -> str:
        lines = [
            f"## Echo Bridge Relay",
            "",
            f"- **Identity:** `{identity}`",
            f"- **Cycle:** `{cycle}`",
            f"- **Signature:** `{signature}`",
        ]
        if traits:
            lines.append("- **Traits:**")
            for key, value in self._sorted_traits(traits):
                lines.append(f"  - `{key}` :: `{value}`")
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
    ) -> str:
        lines = [
            f"Echo Bridge Relay", f"Identity: {identity}", f"Cycle: {cycle}", f"Signature: {signature}",
        ]
        if traits:
            lines.append("Traits:")
            for key, value in self._sorted_traits(traits):
                lines.append(f" - {key}: {value}")
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
    ) -> str:
        fragments: List[str] = [f"Echo Bridge :: {identity}", f"Cycle {cycle}", f"sig {signature}"]
        if summary:
            fragments.append(summary)
        if traits:
            trait_text = ", ".join(f"{key}={value}" for key, value in self._sorted_traits(traits))
            if trait_text:
                fragments.append(trait_text)
        if links:
            fragments.append(" ".join(links[:2]))
        fragments.append("#EchoBridge")
        return " | ".join(fragment for fragment in fragments if fragment)

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
