"""Remote presence layer and identity projection helpers.

This module maintains a rolling window of presence pulses for each identity
and turns that telemetry into projection envelopes.  When an
``EchoBridgeAPI`` instance is available, projection envelopes are converted
into cross-network relay plans; otherwise deterministic fallback plans are
returned so the caller can still act on the identity and presence state.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Iterable, Mapping, MutableMapping, Sequence

from .bridge import BridgePlan, EchoBridgeAPI


@dataclass
class PresencePulse:
    """Single heartbeat from an identity at a point in time."""

    identity: str
    status: str
    channel: str | None = None
    location: str | None = None
    device: str | None = None
    vector: Mapping[str, Any] = field(default_factory=dict)
    observed_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass
class ProjectionEnvelope:
    """Identity projection document paired with relay instructions."""

    identity: str
    cycle: str
    signature: str
    summary: str
    connectors: tuple[str, ...]
    presence_window: tuple[PresencePulse, ...]
    traits: Mapping[str, Any]
    links: tuple[str, ...]
    topics: tuple[str, ...]
    plans: tuple[BridgePlan, ...]


class RemotePresenceLayer:
    """Orchestrate remote presence heartbeats into projection envelopes."""

    def __init__(
        self,
        bridge: EchoBridgeAPI | None = None,
        *,
        default_connectors: Sequence[str] | None = None,
        window_size: int = 25,
    ) -> None:
        self._bridge = bridge
        self._window_size = max(1, window_size)
        self._default_connectors = tuple(
            c.strip().lower()
            for c in (default_connectors or ("webhook", "matrix", "activitypub"))
            if c.strip()
        )
        self._profiles: MutableMapping[str, dict[str, Any]] = {}
        self._presence: MutableMapping[str, deque[PresencePulse]] = {}

    def register_identity(
        self,
        identity: str,
        *,
        persona: str | None = None,
        traits: Mapping[str, Any] | None = None,
        links: Iterable[str] | None = None,
        topics: Iterable[str] | None = None,
        connectors: Iterable[str] | None = None,
    ) -> None:
        """Record the preferred projection metadata for an identity."""

        profile = self._profiles.setdefault(identity, {})
        profile["persona"] = persona or profile.get("persona") or identity
        if traits:
            merged = dict(profile.get("traits", {}))
            merged.update(traits)
            profile["traits"] = merged
        else:
            profile.setdefault("traits", {})
        profile["links"] = tuple(
            link.strip() for link in (links or profile.get("links", ())) if link.strip()
        )
        profile["topics"] = tuple(
            topic.strip().lower()
            for topic in (topics or profile.get("topics", ()))
            if topic.strip()
        )
        profile["connectors"] = self._normalise_connectors(
            connectors or profile.get("connectors") or self._default_connectors
        )

    def ingest_pulse(
        self,
        *,
        identity: str,
        status: str,
        channel: str | None = None,
        location: str | None = None,
        device: str | None = None,
        vector: Mapping[str, Any] | None = None,
        observed_at: datetime | None = None,
    ) -> PresencePulse:
        """Append a presence pulse for the identity."""

        pulse = PresencePulse(
            identity=identity,
            status=status,
            channel=channel,
            location=location,
            device=device,
            vector=dict(vector or {}),
            observed_at=observed_at or datetime.now(timezone.utc),
        )
        window = self._presence.setdefault(
            identity, deque(maxlen=self._window_size)
        )
        window.append(pulse)
        return pulse

    def project_identity(
        self,
        identity: str,
        *,
        cycle: str,
        summary: str | None = None,
        connectors: Iterable[str] | None = None,
    ) -> ProjectionEnvelope:
        """Create a projection envelope for the identity."""

        profile = self._profiles.setdefault(identity, {})
        profile.setdefault("traits", {})
        profile.setdefault("links", ())
        profile.setdefault("topics", ())
        profile.setdefault("connectors", self._default_connectors)

        presence_window = tuple(self._presence.get(identity, ()))
        signature = self._presence_signature(identity, presence_window, profile)
        connectors_tuple = self._normalise_connectors(
            connectors or profile.get("connectors") or self._default_connectors
        )
        summary_text = summary or self._default_summary(identity, presence_window)
        traits = dict(profile.get("traits", {}))
        traits.setdefault("persona", profile.get("persona", identity))
        traits.setdefault(
            "presence_status",
            presence_window[-1].status if presence_window else "unknown",
        )
        links = tuple(profile.get("links", ()))
        topics = tuple(profile.get("topics", ()))

        plans = self._build_plans(
            identity=identity,
            cycle=cycle,
            signature=signature,
            traits=traits,
            summary=summary_text,
            links=links,
            topics=topics,
            connectors=connectors_tuple,
        )

        return ProjectionEnvelope(
            identity=identity,
            cycle=cycle,
            signature=signature,
            summary=summary_text,
            connectors=connectors_tuple,
            presence_window=presence_window,
            traits=traits,
            links=links,
            topics=topics,
            plans=tuple(plans),
        )

    def _presence_signature(
        self,
        identity: str,
        presence_window: Sequence[PresencePulse],
        profile: Mapping[str, Any],
    ) -> str:
        """Build a deterministic digest of recent presence and identity state."""

        payload = {
            "identity": identity,
            "persona": profile.get("persona", identity),
            "traits": profile.get("traits", {}),
            "links": profile.get("links", ()),
            "topics": profile.get("topics", ()),
            "presence": [
                {
                    "status": pulse.status,
                    "channel": pulse.channel,
                    "location": pulse.location,
                    "device": pulse.device,
                    "vector": pulse.vector,
                    "observed_at": pulse.observed_at.isoformat(),
                }
                for pulse in presence_window
            ],
        }
        data = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    def _default_summary(
        self, identity: str, presence_window: Sequence[PresencePulse]
    ) -> str:
        if not presence_window:
            return f"Identity {identity} has no recent presence telemetry."

        latest = presence_window[-1]
        locations = [p.location for p in presence_window if p.location]
        unique_locations = [loc for loc in dict.fromkeys(locations)]
        location_text = ", ".join(unique_locations) if unique_locations else "unspecified"
        return (
            f"Identity {identity} is {latest.status} via {latest.channel or 'direct link'}; "
            f"recent locations: {location_text}."
        )

    def _normalise_connectors(self, connectors: Iterable[str]) -> tuple[str, ...]:
        seen = set()
        normalised = []
        for connector in connectors:
            name = connector.strip().lower()
            if not name or name in seen:
                continue
            seen.add(name)
            normalised.append(name)
        return tuple(normalised)

    def _build_plans(
        self,
        *,
        identity: str,
        cycle: str,
        signature: str,
        traits: Mapping[str, Any],
        summary: str,
        links: Sequence[str],
        topics: Sequence[str],
        connectors: Sequence[str],
    ) -> list[BridgePlan]:
        if self._bridge:
            return self._bridge.plan_identity_relay(
                identity=identity,
                cycle=cycle,
                signature=signature,
                traits=dict(traits),
                summary=summary,
                links=list(links),
                topics=list(topics),
                priority="presence",
                connectors=connectors,
            )

        return [
            BridgePlan(
                platform=connector,
                action="presence_projection",
                payload={
                    "identity": identity,
                    "cycle": cycle,
                    "signature": signature,
                    "summary": summary,
                    "traits": dict(traits),
                    "links": list(links),
                    "topics": list(topics),
                    "priority": "presence",
                },
            )
            for connector in connectors
        ]

