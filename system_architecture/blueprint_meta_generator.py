from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, Iterable, List, Mapping, MutableMapping, Optional


@dataclass
class BlueprintDimension:
    """Represents a computed dimension within the evolving meta-blueprint."""

    name: str
    payload: Mapping[str, object]
    lineage: list[str] = field(default_factory=list)


@dataclass
class LayeredBlueprint:
    """Multi-layer architecture output for the Echo meta-blueprint engine."""

    version: str
    generated_at: datetime
    governance_strata: Mapping[str, object]
    routing_intelligence: Mapping[str, object]
    authority_anchors: Mapping[str, object]
    identity_flow_metrics: Mapping[str, object]
    attestation_mesh_density: Mapping[str, object]
    protocol_lineage: list[str]
    recursion_chains: list[str]
    sovereignty_mesh_density: Mapping[str, object]
    custody_flows: Mapping[str, object]
    dns_authority: Mapping[str, object]
    registrar_mandates: Mapping[str, object]
    dynamic_dimensions: list[BlueprintDimension] = field(default_factory=list)


class MetaBlueprintEngine:
    """Self-expanding generator that recomposes the architecture blueprint on change."""

    def __init__(self) -> None:
        self.subsystems: MutableMapping[str, Dict[str, object]] = {}
        self.dimensions: list[Callable[["MetaBlueprintEngine"], BlueprintDimension]] = []
        self._version_counter = 0
        self._dirty = False

    def register_subsystem(self, name: str, state: Mapping[str, object]) -> None:
        """Register or update a subsystem snapshot."""

        self.subsystems[name] = dict(state)
        self._dirty = True

    def record_change(self, name: str, delta: Mapping[str, object]) -> None:
        """Record a change in any Echo subsystem and trigger regeneration."""

        current = self.subsystems.setdefault(name, {})
        current.update(delta)
        self._dirty = True

    def add_dimension(self, builder: Callable[["MetaBlueprintEngine"], BlueprintDimension]) -> None:
        """Allow the engine to grow new blueprint dimensions dynamically."""

        self.dimensions.append(builder)
        self._dirty = True

    def _next_version(self) -> str:
        self._version_counter += 1
        return f"echo-meta-{self._version_counter:04d}"

    def _compute_mesh_density(self) -> Mapping[str, object]:
        attestations = sum(
            int(meta.get("attestations", 0)) for meta in self.subsystems.values()
        )
        routes = sum(int(meta.get("routes", 0)) for meta in self.subsystems.values())
        authorities = [meta.get("authority") for meta in self.subsystems.values() if meta.get("authority")]

        return {
            "attestation_count": attestations,
            "route_count": routes,
            "sovereign_authorities": authorities,
            "mesh_density": max(attestations, 1) * max(routes, 1),
        }

    def _compute_custody_flows(self) -> Mapping[str, object]:
        flows = {
            name: meta.get("custody", "in-flight") for name, meta in self.subsystems.items()
        }
        return {"flows": flows, "custody_ready": [k for k, v in flows.items() if v == "anchored"]}

    def _compute_dns_authority(self) -> Mapping[str, object]:
        dns = {
            name: meta.get("dns", "pending")
            for name, meta in self.subsystems.items()
            if meta.get("dns") is not None
        }
        return {"records": dns, "registrars": [meta.get("registrar") for meta in self.subsystems.values() if meta.get("registrar")]}

    def _compute_protocol_lineage(self) -> list[str]:
        lineage: list[str] = []
        for name, meta in sorted(self.subsystems.items()):
            proto = meta.get("protocol")
            if proto:
                lineage.append(f"{name}:{proto}")
        return lineage

    def _compute_recursion_chains(self) -> list[str]:
        chains: list[str] = []
        for name, meta in sorted(self.subsystems.items()):
            recursion = meta.get("recursion")
            if recursion:
                chains.append(f"{name}->{recursion}")
        return chains

    def _default_dimensions(self) -> Iterable[BlueprintDimension]:
        yield BlueprintDimension(
            name="routing-sovereignty",
            payload={"routing_intelligence": self._routing_intelligence(), "sovereignty_mesh": self._compute_mesh_density()},
            lineage=["routing", "identity", "attestation"],
        )
        yield BlueprintDimension(
            name="identity-attestation",
            payload={"identity_flow_metrics": self._identity_flow_metrics(), "attestation_mesh_density": self._compute_mesh_density()},
            lineage=["identity", "attestation"],
        )

    def _routing_intelligence(self) -> Mapping[str, object]:
        return {name: meta.get("routes", 0) for name, meta in self.subsystems.items()}

    def _authority_anchors(self) -> Mapping[str, object]:
        return {name: meta.get("authority", "") for name, meta in self.subsystems.items() if meta.get("authority")}

    def _identity_flow_metrics(self) -> Mapping[str, object]:
        metrics = {}
        for name, meta in self.subsystems.items():
            metrics[name] = {
                "dids": meta.get("dids", 0),
                "delegations": meta.get("delegations", 0),
                "issuers": meta.get("issuers", []),
            }
        return metrics

    def _governance_strata(self) -> Mapping[str, object]:
        return {
            name: meta.get("governance", "proposed")
            for name, meta in self.subsystems.items()
        }

    def _registrar_mandates(self) -> Mapping[str, object]:
        return {name: meta.get("mandates", []) for name, meta in self.subsystems.items() if meta.get("mandates")}

    def _compile_dynamic_dimensions(self) -> list[BlueprintDimension]:
        computed: list[BlueprintDimension] = list(self._default_dimensions())
        for builder in self.dimensions:
            computed.append(builder(self))
        return computed

    def regenerate(self) -> LayeredBlueprint:
        """Produce a fresh multi-layer blueprint and reset the change flag."""

        self._dirty = False
        version = self._next_version()
        generated_at = datetime.utcnow()

        dynamic_dimensions = self._compile_dynamic_dimensions()

        return LayeredBlueprint(
            version=version,
            generated_at=generated_at,
            governance_strata=self._governance_strata(),
            routing_intelligence=self._routing_intelligence(),
            authority_anchors=self._authority_anchors(),
            identity_flow_metrics=self._identity_flow_metrics(),
            attestation_mesh_density=self._compute_mesh_density(),
            protocol_lineage=self._compute_protocol_lineage(),
            recursion_chains=self._compute_recursion_chains(),
            sovereignty_mesh_density=self._compute_mesh_density(),
            custody_flows=self._compute_custody_flows(),
            dns_authority=self._compute_dns_authority(),
            registrar_mandates=self._registrar_mandates(),
            dynamic_dimensions=dynamic_dimensions,
        )

    def regenerate_if_changed(self) -> Optional[LayeredBlueprint]:
        """Regenerate the blueprint only when a subsystem delta was recorded."""

        if not self._dirty:
            return None
        return self.regenerate()


def default_meta_engine() -> MetaBlueprintEngine:
    engine = MetaBlueprintEngine()
    engine.register_subsystem(
        "echo_nation",
        {
            "authority": "did:echo:nation:v2:root",
            "dids": 3,
            "delegations": 1,
            "issuers": ["did:echo:nation:v2:issuer"],
            "governance": "sovereign-ledger",
            "attestations": 12,
            "routes": 4,
            "protocol": "vc-ledger",
            "recursion": "ledger->policy->ledger",
            "custody": "anchored",
            "dns": "echo.nation",
            "registrar": "echo-registry",
            "mandates": ["sign-blueprints", "enforce-policy"],
        },
    )
    engine.register_subsystem(
        "blueprint_delta_engine",
        {
            "authority": "did:echo:blueprint:root",
            "dids": 1,
            "delegations": 2,
            "issuers": ["did:echo:blueprint:issuer"],
            "governance": "recursive-meta-blueprint",
            "attestations": 18,
            "routes": 6,
            "protocol": "delta->meta->delta",
            "recursion": "blueprint->worker->blueprint",
            "custody": "anchored",
            "dns": "blueprint.echo",
            "registrar": "echo-registry",
            "mandates": ["enforce-recursion", "register-dimensions"],
        },
    )
    engine.register_subsystem(
        "routing_intelligence",
        {
            "governance": "sovereignty-mesh",
            "attestations": 9,
            "routes": 11,
            "protocol": "mesh->edge->mesh",
            "recursion": "route->attest->route",
            "custody": "in-flight",
            "dns": "route.echo",
        },
    )

    def registrar_dimension(engine: MetaBlueprintEngine) -> BlueprintDimension:
        return BlueprintDimension(
            name="registrar-authority",
            payload={
                "dns_authority": engine._compute_dns_authority(),
                "registrar_mandates": engine._registrar_mandates(),
            },
            lineage=["dns", "registrar"],
        )

    engine.add_dimension(registrar_dimension)
    return engine
