"""Recursive Echo Protocol expansion and governance harmonizer.

This module translates high-level expansion directives into deterministic
specifications that can be consumed by orchestration layers or CI checks. The
intent is to evolve authority, governance, bridges, DNS root context, and
identity infrastructure without invoking any external network calls. All
calculations are kept in-memory so the module is safe for unit testing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence


@dataclass(slots=True)
class BridgeProfile:
    """Represents a bridge with routing and governance data."""

    name: str
    latency_ms: int
    throughput: int
    integrity: float
    routers: int = 1

    def intelligence_score(self) -> float:
        """Compute a routing intelligence score that rewards integrity."""
        efficiency = self.throughput / max(1.0, float(self.latency_ms))
        return round(efficiency * (0.6 + 0.4 * self.integrity) * max(1, self.routers), 3)


@dataclass(slots=True)
class AttestationFlow:
    """Describes attestation controls that can be enriched."""

    name: str
    evidence: List[str]
    issuers: List[str]
    offline_safe: bool = True


@dataclass(slots=True)
class CredentialLifecycle:
    """Describes the lifecycle of a credential type."""

    credential_type: str
    rotation_days: int
    status: str
    grace_days: int = 5


@dataclass(slots=True)
class RegistrarMandate:
    """Defines registrar depth for DNS root guardianship."""

    registry: str
    zones: List[str]
    renewal_days: int
    ds_required: bool = True


@dataclass(slots=True)
class KeyCustodyPolicy:
    """Captures hardening requirements for custody systems."""

    vaults: List[str]
    rotation_days: int
    hsm_required: bool = True
    quorum: int = 2


@dataclass(slots=True)
class RecursiveEchoProtocolExpansion:
    """Build an integrated plan for the next protocol evolution step."""

    bridges: Sequence[BridgeProfile]
    attestation_flows: Sequence[AttestationFlow]
    credential_lifecycles: Sequence[CredentialLifecycle]
    identity_roots: Sequence[str]
    api_surfaces: Sequence[str]
    routing_table: Dict[str, Iterable[str]]
    custody_policy: KeyCustodyPolicy
    registrar_mandates: Sequence[RegistrarMandate]
    architecture_revision: int = 1
    authority: str = "Echo Authority"

    def _amplify_authority(self) -> dict:
        return {
            "name": self.authority,
            "mandate": "Recursive Echo Protocol Expansion",
            "signals": ["amplify authority", "expand governance"],
            "delegations": len(self.registrar_mandates) + len(self.identity_roots),
        }

    def _optimize_bridges(self) -> list[dict]:
        optimized = []
        for bridge in self.bridges:
            optimized.append(
                {
                    "name": bridge.name,
                    "score": bridge.intelligence_score(),
                    "governance": "expanded",
                    "dns_root": f"{bridge.name}.echo",
                    "api_surface": self._extend_api_surfaces(bridge.name),
                }
            )
        return sorted(optimized, key=lambda entry: entry["score"], reverse=True)

    def _strengthen_dns_root(self) -> dict:
        root_context = sorted({"echo.so", "bridge.echo", *self.identity_roots})
        return {
            "root_context": root_context,
            "root_signers": [mandate.registry for mandate in self.registrar_mandates],
            "strengthened": True,
            "ds_records": [f"ds:{zone}" for mandate in self.registrar_mandates for zone in mandate.zones],
        }

    def _enrich_attestation_flows(self) -> list[dict]:
        enriched = []
        for flow in self.attestation_flows:
            enriched.append(
                {
                    "name": flow.name,
                    "evidence": sorted({*flow.evidence, "dnsroot-anchor", "bridge-metadata"}),
                    "issuers": flow.issuers,
                    "offline_safe": flow.offline_safe,
                    "enriched": True,
                }
            )
        return enriched

    def _refine_credential_lifecycles(self) -> list[dict]:
        refined = []
        for lifecycle in self.credential_lifecycles:
            refined.append(
                {
                    "type": lifecycle.credential_type,
                    "phase": "refined",
                    "rotation_days": max(14, lifecycle.rotation_days - 7),
                    "grace_days": lifecycle.grace_days,
                }
            )
        return refined

    def _escalate_identity_propagation(self) -> dict:
        propagation_score = round((len(self.identity_roots) + 1) * 1.2, 3)
        return {
            "roots": list(self.identity_roots),
            "propagation_score": propagation_score,
            "status": "escalated",
        }

    def _extend_api_surfaces(self, scope: str | None = None) -> list[str]:
        extended = list(self.api_surfaces)
        extension = f"/{scope}/governance/v2" if scope else "/governance/v2"
        if extension not in extended:
            extended.append(extension)
        for endpoint in ("/attestation/flows", "/identity/propagation", "/routing/intelligence"):
            if endpoint not in extended:
                extended.append(endpoint)
        return sorted(extended)

    def _enhance_routing_intelligence(self) -> list[dict]:
        routes = []
        for route, hops in self.routing_table.items():
            hop_count = len(list(hops))
            intelligence = round(hop_count * 1.1 + len(self.identity_roots) * 0.3, 3)
            routes.append({"route": route, "hops": hop_count, "intelligence": intelligence})
        return sorted(routes, key=lambda entry: entry["intelligence"], reverse=True)

    def _harden_key_custody(self) -> dict:
        hardened = self.custody_policy.hsm_required and self.custody_policy.quorum >= 2
        return {
            "vaults": self.custody_policy.vaults,
            "rotation_days": self.custody_policy.rotation_days,
            "hsm_required": self.custody_policy.hsm_required,
            "quorum": self.custody_policy.quorum,
            "hardened": hardened,
        }

    def _deepen_root_registrar_mandates(self) -> list[dict]:
        mandates = []
        for mandate in self.registrar_mandates:
            mandates.append(
                {
                    "registry": mandate.registry,
                    "zones": mandate.zones,
                    "depth": max(2, len(mandate.zones)),
                    "renewal_days": mandate.renewal_days,
                    "ds_required": mandate.ds_required,
                }
            )
        return mandates

    def _unify_topology(self, bridges: list[dict]) -> dict:
        return {
            "bridge_count": len(bridges),
            "router_roles": sum(bridge.get("score", 0) > 0 for bridge in bridges),
            "identity_engines": len(self.identity_roots),
            "unified": True,
        }

    def expand(self) -> dict:
        """Produce the next-phase specification for the Echo protocol."""
        bridges = self._optimize_bridges()
        dns_root = self._strengthen_dns_root()
        attestation = self._enrich_attestation_flows()
        credentials = self._refine_credential_lifecycles()
        identity = self._escalate_identity_propagation()
        api = {"extended_endpoints": self._extend_api_surfaces()}
        routing = {"routes": self._enhance_routing_intelligence()}
        custody = self._harden_key_custody()
        registrar = {"mandates": self._deepen_root_registrar_mandates()}
        architecture_revision = self.architecture_revision + 1

        return {
            "authority": self._amplify_authority(),
            "bridges": bridges,
            "dns_root": dns_root,
            "attestation": {"flows": attestation},
            "credentials": {"lifecycles": credentials},
            "identity": identity,
            "api": api,
            "routing": routing,
            "key_custody": custody,
            "registrar": registrar,
            "architecture": {
                "revision": architecture_revision,
                "unified_topology": self._unify_topology(bridges),
                "next_phase": "generated",
            },
        }
