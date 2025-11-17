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
    ) -> None:
        self.github_repository = github_repository
        self.telegram_chat_id = telegram_chat_id
        self.firebase_collection = firebase_collection
        self.slack_webhook_url = slack_webhook_url
        self.slack_channel = slack_channel
        self.slack_secret_name = slack_secret_name
        self.webhook_url = webhook_url
        self.webhook_secret_name = webhook_secret_name

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
