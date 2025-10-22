"""Cross-domain resolver for the PulseNet gateway."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, MutableMapping, Sequence

from echo_atlas.domain import Node

from .models import RegistrationRecord, ResolutionResult


@dataclass(slots=True)
class AtlasProvider:
    """Lightweight adapter around :class:`echo_atlas.service.AtlasService`."""

    service: object

    def list_nodes(self) -> Sequence[Node]:  # pragma: no cover - exercised through service usage
        if hasattr(self.service, "list_nodes"):
            return self.service.list_nodes()
        raise AttributeError("Atlas service must expose list_nodes()")


class CrossDomainResolver:
    """Aggregate atlas, registration, and static sources under one namespace."""

    def __init__(
        self,
        atlas: AtlasProvider,
        registrations: Iterable[RegistrationRecord],
        *,
        config_path: Path | None = None,
    ) -> None:
        self._atlas = atlas
        self._registrations = list(registrations)
        self._config = self._load_config(config_path)

    @staticmethod
    def _load_config(path: Path | None) -> Mapping[str, Mapping[str, Sequence[str]]]:
        if path is None:
            return {}
        config_path = Path(path)
        if not config_path.exists():
            return {}
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return {
            str(namespace): {
                key: tuple(value) if isinstance(value, Sequence) else (str(value),)
                for key, value in mapping.items()
            }
            for namespace, mapping in data.items()
            if isinstance(mapping, Mapping)
        }

    def update_registrations(self, records: Iterable[RegistrationRecord]) -> None:
        self._registrations = list(records)

    def resolve(self, query: str) -> ResolutionResult:
        lower_query = query.lower()
        atlas_matches = [self._serialise_node(node) for node in self._atlas_nodes_matching(lower_query)]
        matching_registrations = [
            record.as_dict() for record in self._registration_matches(lower_query)
        ]
        domains = self._aggregate_domains(lower_query, matching_registrations)
        return ResolutionResult(
            query=query,
            atlas=atlas_matches,
            registrations=matching_registrations,
            domains=domains,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _atlas_nodes_matching(self, lower_query: str) -> Iterable[Node]:
        for node in self._atlas.list_nodes():
            haystacks = [node.identifier.lower(), node.name.lower()]
            for value in node.metadata.values():
                if isinstance(value, str):
                    haystacks.append(value.lower())
                elif isinstance(value, Sequence):
                    haystacks.extend(str(item).lower() for item in value)
            if any(lower_query in haystack for haystack in haystacks):
                yield node

    def _registration_matches(self, lower_query: str) -> Iterable[RegistrationRecord]:
        for record in self._registrations:
            haystacks = [record.name.lower(), record.contact.lower()]
            if record.continuum_handle:
                haystacks.append(record.continuum_handle.lower())
            haystacks.extend(domain.lower() for domain in record.unstoppable_domains)
            haystacks.extend(name.lower() for name in record.ens_names)
            haystacks.extend(project.lower() for project in record.vercel_projects)
            haystacks.extend(wallet.lower() for wallet in record.wallets)
            if any(lower_query in haystack for haystack in haystacks):
                yield record

    def _aggregate_domains(
        self,
        lower_query: str,
        registration_matches: Sequence[Mapping[str, object]],
    ) -> Mapping[str, Sequence[str]]:
        buckets: MutableMapping[str, set[str]] = {
            "unstoppable": set(),
            "ens": set(),
            "vercel": set(),
            "wallets": set(),
        }
        for record in registration_matches:
            for key, bucket in (
                ("unstoppable_domains", "unstoppable"),
                ("ens_names", "ens"),
                ("vercel_projects", "vercel"),
                ("wallets", "wallets"),
            ):
                for value in record.get(key, []) or []:
                    buckets[bucket].add(str(value))
        for namespace, mapping in self._config.items():
            if lower_query not in namespace.lower():
                continue
            for key, values in mapping.items():
                if key not in buckets:
                    continue
                buckets[key].update(str(value) for value in values)
        return {key: tuple(sorted(values)) for key, values in buckets.items()}

    @staticmethod
    def _serialise_node(node: Node) -> Mapping[str, object]:
        payload = node.as_dict()
        payload["entity_type"] = node.entity_type.value
        return payload


__all__ = ["AtlasProvider", "CrossDomainResolver"]
