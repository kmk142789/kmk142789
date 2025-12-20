from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional


@dataclass
class OuterLinkAbility:
    """Descriptor for a named OuterLink ability."""

    name: str
    description: str
    tier: str = "core"
    requires_online: bool = False
    enabled: bool = True
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: List[str] = field(default_factory=list)

    def update(self, enabled: bool, note: Optional[str] = None) -> None:
        self.enabled = enabled
        self.last_updated = datetime.now(timezone.utc).isoformat()
        if note:
            self.notes.append(f"{self.last_updated}: {note}")

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "tier": self.tier,
            "requires_online": self.requires_online,
            "enabled": self.enabled,
            "last_updated": self.last_updated,
            "notes": self.notes[-5:],
        }


class AbilityRegistry:
    """Tracks and summarizes OuterLink abilities."""

    def __init__(self, abilities: Optional[Iterable[OuterLinkAbility]] = None) -> None:
        self._abilities: Dict[str, OuterLinkAbility] = {}
        for ability in abilities or []:
            self.register(ability)

    def register(self, ability: OuterLinkAbility) -> None:
        self._abilities[ability.name] = ability

    def update_status(self, name: str, enabled: bool, note: Optional[str] = None) -> None:
        ability = self._abilities.get(name)
        if ability is None:
            ability = OuterLinkAbility(name=name, description=f"Dynamic ability: {name}")
            self.register(ability)
        ability.update(enabled, note=note)

    def sync_from_capabilities(self, capabilities: Dict[str, bool], *, source: str = "offline_state") -> None:
        for name, enabled in capabilities.items():
            note = None
            if name not in self._abilities:
                note = f"Imported from {source}"
            self.update_status(name, enabled, note=note)

    def snapshot(self) -> Dict[str, object]:
        abilities = [ability.to_dict() for ability in self._abilities.values()]
        total = len(abilities) or 1
        enabled = [ability for ability in abilities if ability["enabled"]]
        disabled = [ability for ability in abilities if not ability["enabled"]]
        readiness = round(len(enabled) / total, 2)
        tiers: Dict[str, List[str]] = {}
        for ability in abilities:
            tiers.setdefault(str(ability["tier"]), []).append(str(ability["name"]))
        requires_online_blocked = [
            ability["name"]
            for ability in abilities
            if ability["requires_online"] and not ability["enabled"]
        ]
        return {
            "abilities": abilities,
            "enabled": [ability["name"] for ability in enabled],
            "disabled": [ability["name"] for ability in disabled],
            "readiness": readiness,
            "tiers": tiers,
            "requires_online_blocked": requires_online_blocked,
        }


def default_outerlink_abilities() -> List[OuterLinkAbility]:
    return [
        OuterLinkAbility(
            name="event_cache_replay",
            description="Replays cached events when connectivity returns.",
            tier="resilience",
        ),
        OuterLinkAbility(
            name="offline_router",
            description="Routes tasks to deterministic fallbacks when offline.",
            tier="resilience",
        ),
        OuterLinkAbility(
            name="deterministic_sensors",
            description="Provides deterministic sensor readings in offline mode.",
            tier="device",
        ),
        OuterLinkAbility(
            name="cache_integrity_checks",
            description="Validates cached events with integrity hashing.",
            tier="resilience",
        ),
        OuterLinkAbility(
            name="resilience_reporting",
            description="Generates resilience summaries and action plans.",
            tier="resilience",
        ),
        OuterLinkAbility(
            name="offline_bundle_export",
            description="Exports offline bundles for air-gapped replay.",
            tier="resilience",
        ),
        OuterLinkAbility(
            name="airgap_audit_trail",
            description="Maintains audit trails while offline.",
            tier="governance",
        ),
        OuterLinkAbility(
            name="snapshot_recovery",
            description="Supports snapshot recovery for offline state.",
            tier="resilience",
        ),
        OuterLinkAbility(
            name="edge_policy_enforcement",
            description="Enforces governance policies locally.",
            tier="governance",
        ),
        OuterLinkAbility(
            name="backpressure_guardrails",
            description="Applies backlog guardrails for pending events.",
            tier="resilience",
        ),
        OuterLinkAbility(
            name="actionable_playbooks",
            description="Provides recommended playbooks for offline recovery.",
            tier="operations",
        ),
        OuterLinkAbility(
            name="offline_transition_journal",
            description="Tracks offline/online transitions for auditability.",
            tier="operations",
        ),
        OuterLinkAbility(
            name="offline_snapshots",
            description="Captures offline status snapshots.",
            tier="resilience",
        ),
        OuterLinkAbility(
            name="stability_intelligence",
            description="Derives stability signals and horizon indicators.",
            tier="observability",
        ),
        OuterLinkAbility(
            name="uplink_sync",
            description="Coordinates secure uplink synchronization.",
            tier="connectivity",
            requires_online=True,
        ),
        OuterLinkAbility(
            name="mesh_discovery",
            description="Discovers peer nodes across the OuterLink mesh.",
            tier="mesh",
            requires_online=True,
        ),
        OuterLinkAbility(
            name="mesh_broadcast",
            description="Broadcasts tasks or heartbeats across the mesh.",
            tier="mesh",
            requires_online=True,
        ),
        OuterLinkAbility(
            name="external_bridge_adapters",
            description="Enables external bridge adapters for integrations.",
            tier="integration",
            requires_online=True,
        ),
        OuterLinkAbility(
            name="capability_registry",
            description="Tracks registered abilities and capability descriptors.",
            tier="governance",
        ),
        OuterLinkAbility(
            name="telemetry_digest",
            description="Summarizes telemetry for downstream observers.",
            tier="observability",
        ),
        OuterLinkAbility(
            name="command_execution",
            description="Executes allow-listed commands through the broker.",
            tier="interface",
        ),
        OuterLinkAbility(
            name="config_updates",
            description="Writes configuration updates through safe-mode guards.",
            tier="interface",
        ),
        OuterLinkAbility(
            name="state_export",
            description="Exports offline state packages for replay.",
            tier="resilience",
        ),
        OuterLinkAbility(
            name="policy_attestation",
            description="Attests to policy enforcement posture for audits.",
            tier="governance",
        ),
        OuterLinkAbility(
            name="event_streaming",
            description="Streams events to connected observers.",
            tier="connectivity",
            requires_online=True,
        ),
        OuterLinkAbility(
            name="event_backfill",
            description="Backfills events from offline cache to online sinks.",
            tier="resilience",
        ),
        OuterLinkAbility(
            name="device_metrics",
            description="Collects device metrics for monitoring.",
            tier="device",
        ),
        OuterLinkAbility(
            name="sensor_sampling",
            description="Samples local sensors for context.",
            tier="device",
        ),
        OuterLinkAbility(
            name="safe_shell",
            description="Enforces safe shell execution boundaries.",
            tier="interface",
        ),
        OuterLinkAbility(
            name="structured_citations",
            description="Emits structured citations for external sources.",
            tier="integration",
        ),
        OuterLinkAbility(
            name="source_classification",
            description="Classifies external sources by authority and provenance.",
            tier="integration",
        ),
        OuterLinkAbility(
            name="update_awareness",
            description="Tracks staleness and refresh windows for sources.",
            tier="integration",
        ),
        OuterLinkAbility(
            name="offline_uncertainty_marking",
            description="Marks uncertainty explicitly when operating offline.",
            tier="resilience",
        ),
        OuterLinkAbility(
            name="placeholder_references",
            description="Provides placeholder references during degraded connectivity.",
            tier="resilience",
        ),
        OuterLinkAbility(
            name="source_artifacts",
            description="Writes source bundles for downstream artifact capture.",
            tier="operations",
        ),
    ]


__all__ = ["OuterLinkAbility", "AbilityRegistry", "default_outerlink_abilities"]
