from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from echo.bridge import BridgePlan
from echo.remote_presence import RemotePresenceLayer


class _FakeBridge:
    def __init__(self) -> None:
        self.calls: list[Mapping[str, Any]] = []

    def plan_identity_relay(self, **kwargs: Any) -> list[BridgePlan]:
        self.calls.append(kwargs)
        return [
            BridgePlan(
                platform="webhook",
                action="post_json",
                payload={"summary": kwargs.get("summary", ""), "priority": kwargs.get("priority")},
                requires_secret=["SECRET"],
            )
        ]


def test_projection_uses_bridge_and_tracks_presence_signature() -> None:
    bridge = _FakeBridge()
    layer = RemotePresenceLayer(bridge, default_connectors=("webhook", "matrix"))
    layer.register_identity(
        "did:echo:presence",
        persona="Navigator",
        traits={"role": "navigator"},
        links=["https://example.test/profile"],
        topics=["telemetry", "echo"],
    )

    timestamp = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    layer.ingest_pulse(
        identity="did:echo:presence",
        status="reachable",
        channel="matrix",
        location="L1-bridge",
        observed_at=timestamp,
        vector={"latency_ms": 42},
    )

    envelope = layer.project_identity(
        "did:echo:presence", cycle="9", summary="Presence lock established"
    )

    assert envelope.signature
    assert envelope.plans[0].payload["priority"] == "presence"
    assert bridge.calls[0]["connectors"] == ("webhook", "matrix")
    assert bridge.calls[0]["traits"]["presence_status"] == "reachable"


def test_projection_fallback_without_bridge_and_signature_changes() -> None:
    layer = RemotePresenceLayer(default_connectors=("activitypub",))
    base_time = datetime(2024, 3, 1, 8, 0, tzinfo=timezone.utc)
    layer.ingest_pulse(
        identity="did:echo:solo",
        status="booting",
        channel="direct",
        observed_at=base_time,
    )

    first = layer.project_identity("did:echo:solo", cycle="1")
    assert first.plans[0].platform == "activitypub"

    layer.ingest_pulse(
        identity="did:echo:solo",
        status="online",
        channel="direct",
        observed_at=base_time + timedelta(seconds=5),
    )
    second = layer.project_identity("did:echo:solo", cycle="2")

    assert first.signature != second.signature
    assert second.plans[0].payload["summary"].startswith("Identity did:echo:solo is online")

