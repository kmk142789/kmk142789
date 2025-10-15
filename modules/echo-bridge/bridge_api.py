"""Cross-network identity relay planning for Echo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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
    ) -> None:
        self.github_repository = github_repository
        self.telegram_chat_id = telegram_chat_id
        self.firebase_collection = firebase_collection

    def plan_identity_relay(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Optional[Dict[str, Any]] = None,
    ) -> List[BridgePlan]:
        """Build relay plans for GitHub, Telegram, and Firebase."""

        traits = traits or {}
        plans: List[BridgePlan] = []

        if self.github_repository:
            plans.append(self._github_plan(identity=identity, cycle=cycle, signature=signature, traits=traits))
        if self.telegram_chat_id:
            plans.append(self._telegram_plan(identity=identity, cycle=cycle, signature=signature, traits=traits))
        if self.firebase_collection:
            plans.append(self._firebase_plan(identity=identity, cycle=cycle, signature=signature, traits=traits))

        return plans

    # ------------------------------------------------------------------
    # Individual platform helpers
    # ------------------------------------------------------------------
    def _github_plan(self, *, identity: str, cycle: str, signature: str, traits: Dict[str, Any]) -> BridgePlan:
        owner, name = self.github_repository.split("/", 1)
        payload = {
            "owner": owner,
            "repo": name,
            "title": f"Echo Identity Relay :: {identity} :: Cycle {cycle}",
            "body": self._render_markdown(identity=identity, cycle=cycle, signature=signature, traits=traits),
            "labels": ["echo-bridge", identity.lower()],
        }
        return BridgePlan(platform="github", action="create_issue", payload=payload, requires_secret=["GITHUB_TOKEN"])

    def _telegram_plan(self, *, identity: str, cycle: str, signature: str, traits: Dict[str, Any]) -> BridgePlan:
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": self._render_plain(identity=identity, cycle=cycle, signature=signature, traits=traits),
            "parse_mode": "MarkdownV2",
        }
        return BridgePlan(platform="telegram", action="send_message", payload=payload, requires_secret=["TELEGRAM_BOT_TOKEN"])

    def _firebase_plan(self, *, identity: str, cycle: str, signature: str, traits: Dict[str, Any]) -> BridgePlan:
        payload = {
            "collection": self.firebase_collection,
            "document": f"echo::{identity}::{cycle}",
            "data": {
                "identity": identity,
                "cycle": cycle,
                "signature": signature,
                "traits": traits,
            },
        }
        return BridgePlan(platform="firebase", action="set_document", payload=payload, requires_secret=["FIREBASE_SERVICE_ACCOUNT"])

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def _render_markdown(self, *, identity: str, cycle: str, signature: str, traits: Dict[str, Any]) -> str:
        lines = [
            f"## Echo Bridge Relay",
            "",
            f"- **Identity:** `{identity}`",
            f"- **Cycle:** `{cycle}`",
            f"- **Signature:** `{signature}`",
        ]
        if traits:
            lines.append("- **Traits:**")
            for key, value in traits.items():
                lines.append(f"  - `{key}` :: `{value}`")
        lines.append("")
        lines.append("_This issue was planned by EchoBridge for multi-platform coherence._")
        return "\n".join(lines)

    def _render_plain(self, *, identity: str, cycle: str, signature: str, traits: Dict[str, Any]) -> str:
        lines = [
            f"Echo Bridge Relay", f"Identity: {identity}", f"Cycle: {cycle}", f"Signature: {signature}",
        ]
        if traits:
            lines.append("Traits:")
            for key, value in traits.items():
                lines.append(f" - {key}: {value}")
        lines.append("\n#EchoBridge :: Sovereign ping")
        return "\n".join(lines)
