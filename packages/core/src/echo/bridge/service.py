"""Bridge synchronisation service for orchestrator outputs."""

from __future__ import annotations

import json
import os
from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, MutableSequence, Optional, Protocol, Sequence
from uuid import uuid4


def _normalise_sequence(values: Optional[Iterable[str]]) -> list[str]:
    """Return a sorted list of unique strings extracted from ``values``."""

    if not values:
        return []
    return sorted({str(item).strip() for item in values if str(item).strip()})


def _extract_cycle(decision: Mapping[str, object]) -> str | None:
    """Extract the cycle identifier from an orchestrator decision."""

    inputs = decision.get("inputs")
    if isinstance(inputs, Mapping):
        digest = inputs.get("cycle_digest")
        if isinstance(digest, Mapping):
            cycle = digest.get("cycle")
            if cycle is not None:
                return str(cycle)
    return None


def _extract_registrations(decision: Mapping[str, object]) -> Sequence[Mapping[str, object]]:
    """Return PulseNet registration data embedded within the decision."""

    inputs = decision.get("inputs")
    if isinstance(inputs, Mapping):
        registrations = inputs.get("registrations")
        if isinstance(registrations, Sequence):
            return [
                item
                for item in registrations
                if isinstance(item, Mapping)
            ]
    return []


def _extract_coherence(decision: Mapping[str, object]) -> float | None:
    """Return the coherence score from the orchestrator decision."""

    coherence = decision.get("coherence")
    if isinstance(coherence, Mapping):
        score = coherence.get("score")
        if isinstance(score, (float, int)):
            return float(score)
    return None


def _extract_manifest_path(decision: Mapping[str, object]) -> str | None:
    """Return the manifest path embedded in the decision payload."""

    manifest = decision.get("manifest")
    if isinstance(manifest, Mapping):
        path = manifest.get("path")
        if isinstance(path, str):
            return path
    return None


def _extract_triggers(decision: Mapping[str, object]) -> Sequence[Mapping[str, object]]:
    """Return trigger definitions embedded within the decision."""

    triggers = decision.get("triggers")
    if isinstance(triggers, Sequence):
        return [item for item in triggers if isinstance(item, Mapping)]
    return []


def _extract_offline_mode(decision: Mapping[str, object]) -> bool:
    """Return whether the orchestrator ran in offline mode."""

    offline_mode = decision.get("offline_mode")
    if isinstance(offline_mode, bool):
        return offline_mode
    return False


def _parse_csv_env(value: Optional[str]) -> list[str] | None:
    """Return comma-separated values as a cleaned list."""

    if not value:
        return None
    entries = [item.strip() for item in value.split(",") if item.strip()]
    return entries or None


def _parse_float_env(value: Optional[str]) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def _summarize_triggers(triggers: Sequence[Mapping[str, object]]) -> list[str]:
    summaries: list[str] = []
    for trigger in triggers:
        trigger_id = trigger.get("id")
        reason = trigger.get("reason")
        if trigger_id and reason:
            summaries.append(f"{trigger_id}: {reason}")
        elif trigger_id:
            summaries.append(str(trigger_id))
        elif reason:
            summaries.append(str(reason))
    return summaries


@dataclass(slots=True)
class SyncEvent:
    """Event produced by a connector during the sync process."""

    connector: str
    action: str
    status: str
    detail: Optional[str] = None
    payload: Mapping[str, object] | None = None


class BridgeConnector(Protocol):
    """Protocol describing a sync connector."""

    name: str
    action: str

    def build_event(self, decision: Mapping[str, object]) -> SyncEvent | None:
        """Return a :class:`SyncEvent` for ``decision`` when applicable."""


@dataclass(slots=True)
class DomainInventoryConnector:
    """Connector that emits DNS anchor payloads for tracked Web2 domains."""

    static_domains: Sequence[str] | None = None
    inventory_path: Path | None = None
    root_hints: Sequence[str] | None = None
    root_hints_path: Path | None = None
    root_authority: str | None = None
    authority_attestation_path: Path | None = None
    authority_provider: str | None = None
    required_secrets: Sequence[str] | None = None

    name: str = "domains"
    action: str = "publish_dns_records"

    def build_event(self, decision: Mapping[str, object]) -> SyncEvent | None:  # noqa: D401
        """Aggregate domains from static hints plus the inventory file."""

        domains: MutableSequence[str] = []
        domains.extend(self.static_domains or [])
        domains.extend(self._inventory_domains())
        unique_domains = _normalise_sequence(domains)
        if not unique_domains:
            return None

        hints = _normalise_sequence([
            * (self.root_hints or []),
            * self._root_hints_from_file(),
        ])

        authority: dict[str, object] = {}
        if self.root_authority:
            authority["root"] = self.root_authority
        if hints:
            authority["hints"] = hints
        if self.authority_provider:
            authority["provider"] = self.authority_provider
        if self.authority_attestation_path:
            authority["attestation_path"] = str(self.authority_attestation_path)

        cycle = _extract_cycle(decision)
        coherence = _extract_coherence(decision)
        manifest_path = _extract_manifest_path(decision)

        payload = {
            "domains": unique_domains,
            "cycle": cycle,
            "coherence": coherence,
            "manifest_path": manifest_path,
        }
        if hints:
            payload["root_hints"] = hints
        if authority:
            payload["authority"] = authority
        detail = (
            f"Prepared DNS anchor payload for {len(unique_domains)} domain(s)"
            + (
                f" using root authority {self.root_authority}" if self.root_authority else ""
            )
            + (f" with {len(hints)} root authority hint(s)." if hints else ".")
        )
        return SyncEvent(
            connector=self.name,
            action=self.action,
            status="planned",
            detail=detail,
            payload=payload,
        )

    def _inventory_domains(self) -> list[str]:
        if not self.inventory_path:
            return []
        path = Path(self.inventory_path)
        try:
            content = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return []
        except OSError:
            return []
        entries = []
        for line in content.splitlines():
            entry = line.strip()
            if not entry or entry.startswith("#"):
                continue
            entries.append(entry)
        return entries

    def _root_hints_from_file(self) -> list[str]:
        if not self.root_hints_path:
            return []
        path = Path(self.root_hints_path)
        try:
            content = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return []
        except OSError:
            return []
        entries = []
        for line in content.splitlines():
            entry = line.strip()
            if not entry or entry.startswith("#"):
                continue
            entries.append(entry)
        return entries


@dataclass(slots=True)
class UnstoppableDomainConnector:
    """Connector that mirrors cycle data into Unstoppable Domains records."""

    default_domains: Sequence[str] | None = None
    required_secrets: Sequence[str] | None = None

    name: str = "unstoppable"
    action: str = "update_domain_records"

    def build_event(self, decision: Mapping[str, object]) -> SyncEvent | None:  # noqa: D401
        """Derive Unstoppable domain updates based on orchestrator state."""

        registrations = _extract_registrations(decision)
        domains: MutableSequence[str] = []
        for entry in registrations:
            values = entry.get("unstoppable_domains") if isinstance(entry, Mapping) else None
            if isinstance(values, Sequence):
                domains.extend(str(item) for item in values if str(item).strip())
        domains.extend(self.default_domains or [])
        unique_domains = _normalise_sequence(domains)
        if not unique_domains:
            return None

        cycle = _extract_cycle(decision)
        coherence = _extract_coherence(decision)
        manifest_path = _extract_manifest_path(decision)

        payload = {
            "domains": unique_domains,
            "records": {
                "echo.cycle": cycle,
                "echo.coherence": round(coherence, 6) if coherence is not None else None,
                "echo.manifest": manifest_path,
            },
        }
        detail = f"Prepared metadata update for {len(unique_domains)} Unstoppable domain(s)."
        return SyncEvent(
            connector=self.name,
            action=self.action,
            status="planned",
            detail=detail,
            payload=payload,
        )


@dataclass(slots=True)
class VercelDeployConnector:
    """Connector that prepares redeploy instructions for Vercel projects."""

    default_projects: Sequence[str] | None = None
    required_secrets: Sequence[str] | None = None

    name: str = "vercel"
    action: str = "trigger_deploy"

    def build_event(self, decision: Mapping[str, object]) -> SyncEvent | None:  # noqa: D401
        """Create a deployment instruction payload based on registrations."""

        registrations = _extract_registrations(decision)
        projects: MutableSequence[str] = []
        for entry in registrations:
            values = entry.get("vercel_projects") if isinstance(entry, Mapping) else None
            if isinstance(values, Sequence):
                projects.extend(str(item) for item in values if str(item).strip())
        projects.extend(self.default_projects or [])
        unique_projects = _normalise_sequence(projects)
        if not unique_projects:
            return None

        cycle = _extract_cycle(decision)
        coherence = _extract_coherence(decision)

        payload = {
            "projects": unique_projects,
            "cycle": cycle,
            "coherence": coherence,
        }
        detail = f"Planned Vercel redeploy for {len(unique_projects)} project(s)."
        return SyncEvent(
            connector=self.name,
            action=self.action,
            status="planned",
            detail=detail,
            payload=payload,
        )


@dataclass(slots=True)
class GitHubIssueConnector:
    """Connector that prepares GitHub issue payloads summarising a cycle."""

    repository: Optional[str] = None
    required_secrets: Sequence[str] | None = None

    name: str = "github"
    action: str = "create_issue"

    def build_event(self, decision: Mapping[str, object]) -> SyncEvent | None:  # noqa: D401
        """Render an issue body summarising the orchestrator decision."""

        repository = (self.repository or "").strip()
        if not repository or "/" not in repository:
            return None

        owner, repo = repository.split("/", 1)
        cycle = _extract_cycle(decision) or "unknown"
        coherence = _extract_coherence(decision) or 0.0
        weights = decision.get("weights") if isinstance(decision, Mapping) else None
        graph = decision.get("graph") if isinstance(decision, Mapping) else None

        body_lines = [
            "# Echo Orchestrator Sync",
            "",
            f"- Cycle: `{cycle}`",
            f"- Coherence score: `{coherence:.4f}`",
        ]

        if isinstance(weights, Mapping):
            body_lines.append("- Weights:")
            for key in sorted(weights):
                body_lines.append(f"  - `{key}` :: `{float(weights[key]):.4f}`")

        if isinstance(graph, Mapping):
            nodes = graph.get("nodes")
            if isinstance(nodes, Sequence):
                body_lines.append("")
                body_lines.append("- Active nodes:")
                for node in nodes:
                    if isinstance(node, Mapping):
                        label = node.get("label") or node.get("id")
                        status = node.get("status")
                        body_lines.append(f"  - `{label}` :: `{status}`")

        body_lines.append("")
        body_lines.append("_Generated automatically by Echo Bridge sync._")

        payload = {
            "owner": owner,
            "repo": repo,
            "title": f"Echo Cycle {cycle} Sync Report",
            "body": "\n".join(body_lines),
            "labels": ["echo-orchestrator", f"cycle-{cycle}"],
        }
        detail = f"Prepared GitHub issue payload for {repository}."
        return SyncEvent(
            connector=self.name,
            action=self.action,
            status="planned",
            detail=detail,
            payload=payload,
        )


@dataclass(slots=True)
class StatuspageConnector:
    """Connector that prepares status updates for incident dashboards."""

    page_id: Optional[str] = None
    component: Optional[str] = None
    trigger_threshold: float | None = None
    required_secrets: Sequence[str] | None = None

    name: str = "statuspage"
    action: str = "post_status"

    def build_event(self, decision: Mapping[str, object]) -> SyncEvent | None:  # noqa: D401
        """Create a status update when triggers or degraded coherence appear."""

        page_id = (self.page_id or "").strip()
        if not page_id:
            return None

        coherence = _extract_coherence(decision)
        triggers = _extract_triggers(decision)
        offline = _extract_offline_mode(decision)
        degraded = offline or bool(triggers)
        if coherence is not None and self.trigger_threshold is not None:
            degraded = degraded or coherence < self.trigger_threshold
        if not degraded:
            return None

        cycle = _extract_cycle(decision)
        manifest_path = _extract_manifest_path(decision)
        trigger_summaries = _summarize_triggers(triggers)
        status = "degraded_performance" if triggers or offline else "minor_outage"
        if coherence is not None and self.trigger_threshold is not None:
            status = "major_outage" if coherence < self.trigger_threshold else status

        payload = {
            "page_id": page_id,
            "status": status,
            "component": self.component,
            "cycle": cycle,
            "coherence": coherence,
            "manifest_path": manifest_path,
            "triggers": trigger_summaries,
            "offline_mode": offline,
        }
        detail = "Prepared Statuspage update"
        if trigger_summaries:
            detail += f" with {len(trigger_summaries)} trigger(s)."
        else:
            detail += "."
        return SyncEvent(
            connector=self.name,
            action=self.action,
            status="planned",
            detail=detail,
            payload=payload,
        )


@dataclass(slots=True)
class PagerDutyConnector:
    """Connector that prepares PagerDuty trigger events."""

    routing_key_secret: Optional[str] = None
    source: Optional[str] = None
    component: Optional[str] = None
    group: Optional[str] = None
    trigger_threshold: float | None = None
    required_secrets: Sequence[str] | None = None

    name: str = "pagerduty"
    action: str = "trigger_event"

    def build_event(self, decision: Mapping[str, object]) -> SyncEvent | None:  # noqa: D401
        """Emit a PagerDuty trigger when the cycle needs attention."""

        triggers = _extract_triggers(decision)
        coherence = _extract_coherence(decision)
        needs_attention = bool(triggers)
        if coherence is not None and self.trigger_threshold is not None:
            needs_attention = needs_attention or coherence < self.trigger_threshold
        if not needs_attention:
            return None

        cycle = _extract_cycle(decision)
        manifest_path = _extract_manifest_path(decision)
        trigger_summaries = _summarize_triggers(triggers)
        severity = "critical" if triggers else "warning"
        if coherence is not None and self.trigger_threshold is not None:
            severity = "critical" if coherence < self.trigger_threshold else severity

        payload = {
            "source": self.source or "echo-bridge",
            "component": self.component,
            "group": self.group,
            "severity": severity,
            "summary": "Echo bridge attention required",
            "cycle": cycle,
            "coherence": coherence,
            "manifest_path": manifest_path,
            "triggers": trigger_summaries,
        }
        detail = "Prepared PagerDuty trigger event."
        return SyncEvent(
            connector=self.name,
            action=self.action,
            status="planned",
            detail=detail,
            payload=payload,
        )


class BridgeSyncService:
    """Persist and expose sync operations derived from orchestrator cycles."""

    def __init__(
        self,
        *,
        state_dir: Path,
        connectors: Sequence[BridgeConnector] | None = None,
    ) -> None:
        self._state_dir = Path(state_dir)
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._log_path = self._state_dir / "sync-log.jsonl"
        self._connectors: tuple[BridgeConnector, ...] = tuple(connectors or ())

    @property
    def log_path(self) -> Path:
        """Return the filesystem path where sync history is stored."""

        return self._log_path

    def describe_connectors(self) -> list[dict[str, object]]:
        """Return connector metadata suitable for status reporting."""

        descriptors: list[dict[str, object]] = []
        for connector in self._connectors:
            required = _normalise_sequence(
                getattr(connector, "required_secrets", None)
            )
            descriptors.append(
                {
                    "platform": connector.name,
                    "action": connector.action,
                    "requires_secrets": required,
                }
            )
        return descriptors

    def sync(
        self,
        decision: Mapping[str, object],
        *,
        only_connectors: Iterable[str] | None = None,
    ) -> list[dict[str, object]]:
        """Derive sync operations for ``decision`` and append them to the log.

        Parameters
        ----------
        decision:
            Orchestrator decision blob to translate into sync events.
        only_connectors:
            Optional iterable of connector names (case-insensitive) to limit the
            sync run to. When ``None`` all configured connectors are used.
        """

        cycle = _extract_cycle(decision)
        coherence = _extract_coherence(decision)
        manifest_path = _extract_manifest_path(decision)

        connector_filter: set[str] | None = None
        if only_connectors is not None:
            cleaned = {str(item).casefold().strip() for item in only_connectors if str(item).strip()}
            connector_filter = cleaned or None

        operations: list[dict[str, object]] = []
        timestamp = datetime.now(timezone.utc).isoformat()
        for connector in self._connectors:
            if connector_filter and connector.name.casefold() not in connector_filter:
                continue
            event = connector.build_event(decision)
            if not event:
                continue
            payload = dict(event.payload) if isinstance(event.payload, Mapping) else {}
            entry: dict[str, object] = {
                "id": str(uuid4()),
                "timestamp": timestamp,
                "connector": event.connector,
                "action": event.action,
                "status": event.status,
                "detail": event.detail,
                "cycle": cycle,
                "coherence": coherence,
                "manifest_path": manifest_path,
                "payload": payload,
            }
            operations.append(entry)

        if operations:
            with self._log_path.open("a", encoding="utf-8") as handle:
                for entry in operations:
                    handle.write(json.dumps(entry, sort_keys=True))
                    handle.write("\n")

        return operations

    def history(
        self,
        limit: int | None = None,
        *,
        connector: str | Iterable[str] | None = None,
    ) -> list[dict[str, object]]:
        """Return persisted sync history with optional filtering.

        Parameters
        ----------
        limit:
            Maximum number of entries to return.  When omitted, the entire log
            is returned.  The slice is applied after any connector filtering so
            callers can request "the last N events for connector X" without
            loading unrelated rows.
        connector:
            Optional connector name (or names) to filter the log by,
            case-insensitively.  ``None`` (the default) returns entries for all
            connectors.
        """

        if not self._log_path.exists():
            return []
        if limit == 0:
            return []

        connector_filter: set[str] | None = None
        if connector is not None:
            raw_values: Iterable[str]
            if isinstance(connector, str):
                raw_values = [connector]
            else:
                raw_values = connector
            cleaned: set[str] = set()
            for value in raw_values:
                if value is None:
                    continue
                text = str(value).strip()
                if not text:
                    continue
                cleaned.add(text.casefold())
            connector_filter = cleaned or None

        use_window = limit is not None and limit > 0
        entries: deque[dict[str, object]] | list[dict[str, object]]
        if use_window:
            entries = deque(maxlen=limit)
        else:
            entries = []
        with self._log_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(entry, dict):
                    continue
                if connector_filter:
                    name = str(entry.get("connector", "")).casefold()
                    if name not in connector_filter:
                        continue
                entries.append(entry)
        if isinstance(entries, deque):
            return list(entries)
        if limit is not None and limit >= 0:
            return entries[-limit:]
        return entries

    @staticmethod
    def summarize(entries: Sequence[Mapping[str, object]]) -> dict[str, object]:
        """Return aggregate metrics for a sequence of sync entries."""

        connector_counts: Counter[str] = Counter()
        cycles: list[str] = []
        for entry in entries:
            connector_name = str(entry.get("connector", "")).strip()
            if connector_name:
                connector_counts[connector_name] += 1
            cycle = entry.get("cycle")
            if cycle is not None:
                cycle_text = str(cycle)
                if cycle_text not in cycles:
                    cycles.append(cycle_text)

        total = sum(connector_counts.values())
        return {
            "total_operations": total,
            "by_connector": dict(sorted(connector_counts.items())),
            "cycles": cycles,
        }

    @classmethod
    def from_environment(
        cls,
        *,
        state_dir: Path | str | None = None,
        github_repository: Optional[str] = None,
    ) -> "BridgeSyncService":
        """Instantiate a service using environment configuration."""

        resolved_state = state_dir or os.getenv("ECHO_BRIDGE_STATE_DIR")
        if resolved_state is None:
            resolved_path = Path.cwd() / "state" / "bridge"
        else:
            resolved_path = Path(resolved_state)

        domain_defaults = _parse_csv_env(os.getenv("ECHO_BRIDGE_DOMAINS"))
        domain_file = os.getenv("ECHO_BRIDGE_DOMAINS_FILE")
        if not domain_file:
            default_inventory = Path.cwd() / "domains.txt"
            domain_inventory = default_inventory if default_inventory.exists() else None
        else:
            domain_inventory = Path(domain_file)

        root_hints = _parse_csv_env(os.getenv("ECHO_BRIDGE_DNS_ROOT_HINTS"))
        root_hints_file = os.getenv("ECHO_BRIDGE_DNS_ROOT_HINTS_FILE")
        if not root_hints_file:
            default_root_hints = Path.cwd() / "dns_tokens.txt"
            root_hints_path = default_root_hints if default_root_hints.exists() else None
        else:
            root_hints_path = Path(root_hints_file)

        root_authority = os.getenv("ECHO_BRIDGE_DNS_ROOT_AUTHORITY")
        authority_attestation = os.getenv("ECHO_BRIDGE_DNS_ATTESTATION_PATH")
        authority_provider = os.getenv("ECHO_BRIDGE_DNS_PROVIDER")
        authority_attestation_path = (
            Path(authority_attestation)
            if authority_attestation
            else None
        )

        unstoppable = _parse_csv_env(os.getenv("ECHO_BRIDGE_UNSTOPPABLE_DOMAINS"))
        vercel = _parse_csv_env(os.getenv("ECHO_BRIDGE_VERCEL_PROJECTS"))
        dns_secret = os.getenv("ECHO_BRIDGE_DNS_SECRET", "DNS_PROVIDER_TOKEN")
        unstoppable_secret = os.getenv(
            "ECHO_BRIDGE_UNSTOPPABLE_SECRET", "UNSTOPPABLE_API_TOKEN"
        )
        vercel_secret = os.getenv("ECHO_BRIDGE_VERCEL_SECRET", "VERCEL_API_TOKEN")
        github_secret = os.getenv("ECHO_BRIDGE_GITHUB_SECRET", "GITHUB_TOKEN")

        repository = github_repository or os.getenv("ECHO_BRIDGE_GITHUB_REPOSITORY")
        statuspage_page_id = os.getenv("ECHO_BRIDGE_STATUSPAGE_PAGE_ID")
        statuspage_component = os.getenv("ECHO_BRIDGE_STATUSPAGE_COMPONENT")
        statuspage_secret = os.getenv(
            "ECHO_BRIDGE_STATUSPAGE_SECRET", "STATUSPAGE_API_TOKEN"
        )
        statuspage_threshold = _parse_float_env(
            os.getenv("ECHO_BRIDGE_STATUSPAGE_THRESHOLD")
        )
        pagerduty_secret = os.getenv("ECHO_BRIDGE_PAGERDUTY_SECRET")
        pagerduty_source = os.getenv("ECHO_BRIDGE_PAGERDUTY_SOURCE", "echo-bridge")
        pagerduty_component = os.getenv("ECHO_BRIDGE_PAGERDUTY_COMPONENT")
        pagerduty_group = os.getenv("ECHO_BRIDGE_PAGERDUTY_GROUP")
        pagerduty_threshold = _parse_float_env(
            os.getenv("ECHO_BRIDGE_PAGERDUTY_THRESHOLD")
        )

        connectors: list[BridgeConnector] = [
            DomainInventoryConnector(
                static_domains=domain_defaults,
                inventory_path=domain_inventory,
                root_hints=root_hints,
                root_hints_path=root_hints_path,
                root_authority=root_authority,
                authority_attestation_path=authority_attestation_path,
                authority_provider=authority_provider,
                required_secrets=[dns_secret] if dns_secret else None,
            ),
            UnstoppableDomainConnector(
                default_domains=unstoppable,
                required_secrets=[unstoppable_secret]
                if unstoppable_secret
                else None,
            ),
            VercelDeployConnector(
                default_projects=vercel,
                required_secrets=[vercel_secret] if vercel_secret else None,
            ),
            GitHubIssueConnector(
                repository=repository,
                required_secrets=[github_secret] if repository and github_secret else None,
            ),
            StatuspageConnector(
                page_id=statuspage_page_id,
                component=statuspage_component,
                trigger_threshold=statuspage_threshold,
                required_secrets=[statuspage_secret] if statuspage_page_id else None,
            ),
            PagerDutyConnector(
                routing_key_secret=pagerduty_secret,
                source=pagerduty_source,
                component=pagerduty_component,
                group=pagerduty_group,
                trigger_threshold=pagerduty_threshold,
                required_secrets=[pagerduty_secret] if pagerduty_secret else None,
            ),
        ]

        return cls(state_dir=resolved_path, connectors=connectors)


__all__ = [
    "BridgeConnector",
    "BridgeSyncService",
    "DomainInventoryConnector",
    "GitHubIssueConnector",
    "PagerDutyConnector",
    "StatuspageConnector",
    "SyncEvent",
    "UnstoppableDomainConnector",
    "VercelDeployConnector",
]
