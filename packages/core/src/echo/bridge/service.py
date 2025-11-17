"""Bridge synchronisation service for orchestrator outputs."""

from __future__ import annotations

import json
import os
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


def _parse_csv_env(value: Optional[str]) -> list[str] | None:
    """Return comma-separated values as a cleaned list."""

    if not value:
        return None
    entries = [item.strip() for item in value.split(",") if item.strip()]
    return entries or None


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

        cycle = _extract_cycle(decision)
        coherence = _extract_coherence(decision)
        manifest_path = _extract_manifest_path(decision)

        payload = {
            "domains": unique_domains,
            "cycle": cycle,
            "coherence": coherence,
            "manifest_path": manifest_path,
        }
        detail = f"Prepared DNS anchor payload for {len(unique_domains)} domain(s)."
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


@dataclass(slots=True)
class UnstoppableDomainConnector:
    """Connector that mirrors cycle data into Unstoppable Domains records."""

    default_domains: Sequence[str] | None = None

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

    def sync(self, decision: Mapping[str, object]) -> list[dict[str, object]]:
        """Derive sync operations for ``decision`` and append them to the log."""

        cycle = _extract_cycle(decision)
        coherence = _extract_coherence(decision)
        manifest_path = _extract_manifest_path(decision)

        operations: list[dict[str, object]] = []
        timestamp = datetime.now(timezone.utc).isoformat()
        for connector in self._connectors:
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

    def history(self, limit: int | None = None) -> list[dict[str, object]]:
        """Return persisted sync history, optionally constrained by ``limit``."""

        if not self._log_path.exists():
            return []

        entries: list[dict[str, object]] = []
        with self._log_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(entry, dict):
                    entries.append(entry)
        if limit is not None and limit >= 0:
            entries = entries[-limit:]
        return entries

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

        unstoppable = _parse_csv_env(os.getenv("ECHO_BRIDGE_UNSTOPPABLE_DOMAINS"))
        vercel = _parse_csv_env(os.getenv("ECHO_BRIDGE_VERCEL_PROJECTS"))

        repository = github_repository or os.getenv("ECHO_BRIDGE_GITHUB_REPOSITORY")

        connectors: list[BridgeConnector] = [
            DomainInventoryConnector(
                static_domains=domain_defaults,
                inventory_path=domain_inventory,
            ),
            UnstoppableDomainConnector(default_domains=unstoppable),
            VercelDeployConnector(default_projects=vercel),
            GitHubIssueConnector(repository=repository),
        ]

        return cls(state_dir=resolved_path, connectors=connectors)


__all__ = [
    "BridgeConnector",
    "BridgeSyncService",
    "DomainInventoryConnector",
    "GitHubIssueConnector",
    "SyncEvent",
    "UnstoppableDomainConnector",
    "VercelDeployConnector",
]
