"""Identity flow audit utilities.

This module provides helpers to inspect identity flow payloads for internal
consistency.  Each flow consists of a set of nodes (entities) and directed
claims between them.  The :func:`audit_identity_flow` entry point analyses the
payload and reports three categories of issues:

* **Contradictions** – multiple claims that disagree about the same attribute
  for a given target identity.
* **Mismatches** – structural or attribute mismatches between a claim and the
  declared node metadata.
* **Unverifiable assertions** – claims that lack sufficient proof material to
  validate.

The utilities are intentionally conservative: any ambiguity is surfaced so the
caller can perform additional review before trusting the identity flow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping
import json


def _canonicalise_value(value: Any) -> str:
    """Return a deterministic string representation for *value*."""

    if isinstance(value, (dict, list, tuple)):
        try:
            return json.dumps(value, sort_keys=True)
        except (TypeError, ValueError):  # pragma: no cover - defensive fallback
            return repr(value)
    return repr(value)


@dataclass
class IdentityNode:
    """Represents an identity participating in the flow."""

    did: str
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IdentityClaim:
    """Directed claim describing a relationship or attribute assertion."""

    id: str
    source: str
    target: str
    attribute: str
    value: Any
    proof: str | None = None
    expected: Dict[str, Any] = field(default_factory=dict)
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IdentityFlow:
    """Container for identity nodes and the claims between them."""

    nodes: Dict[str, IdentityNode]
    claims: list[IdentityClaim]

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def claim_count(self) -> int:
        return len(self.claims)


@dataclass
class IdentityFlowReport:
    """Aggregated outcome of auditing an identity flow."""

    nodes_evaluated: int
    claims_evaluated: int
    contradictions: list[str] = field(default_factory=list)
    mismatches: list[str] = field(default_factory=list)
    unverifiable: list[str] = field(default_factory=list)

    def is_healthy(self) -> bool:
        """Return ``True`` if no issues were detected."""

        return not (self.contradictions or self.mismatches or self.unverifiable)

    def render_text(self) -> str:
        """Render a human-readable representation of the audit results."""

        lines = [
            "Echo Identity Flow Audit",
            f"Nodes evaluated: {self.nodes_evaluated}",
            f"Claims evaluated: {self.claims_evaluated}",
            f"Contradictions: {len(self.contradictions)}",
            f"Mismatches: {len(self.mismatches)}",
            f"Unverifiable assertions: {len(self.unverifiable)}",
        ]

        if self.contradictions:
            lines.append("")
            lines.append("Contradictions detected:")
            lines.extend(f"- {message}" for message in self.contradictions)

        if self.mismatches:
            lines.append("")
            lines.append("Mismatched data:")
            lines.extend(f"- {message}" for message in self.mismatches)

        if self.unverifiable:
            lines.append("")
            lines.append("Unverifiable assertions:")
            lines.extend(f"- {message}" for message in self.unverifiable)

        return "\n".join(lines)


def load_identity_flow(path: Path | str) -> IdentityFlow:
    """Load an :class:`IdentityFlow` from *path*."""

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    nodes: Dict[str, IdentityNode] = {}
    for node in raw.get("nodes", []):
        if not isinstance(node, Mapping):
            continue
        did = node.get("id")
        if not isinstance(did, str):
            continue
        attributes = {
            key: node[key]
            for key in node
            if key != "id"
        }
        nodes[did] = IdentityNode(did=did, attributes=attributes)

    claims: list[IdentityClaim] = []
    for index, claim in enumerate(raw.get("claims", []), start=1):
        if not isinstance(claim, Mapping):
            continue
        source = claim.get("source")
        target = claim.get("target")
        attribute = claim.get("attribute", "status")
        if not all(isinstance(item, str) for item in (source, target, attribute)):
            continue
        claim_id = claim.get("id")
        if not isinstance(claim_id, str):
            claim_id = f"claim-{index}"
        proof = claim.get("proof")
        if isinstance(proof, str):
            proof = proof.strip() or None
        else:
            proof = None

        expected = claim.get("expected")
        if isinstance(expected, Mapping):
            expected_payload = {str(key): expected[key] for key in expected}
        else:
            expected_payload = {}

        evidence = claim.get("evidence")
        if isinstance(evidence, Mapping):
            evidence_payload = {str(key): evidence[key] for key in evidence}
        else:
            evidence_payload = {}

        claims.append(
            IdentityClaim(
                id=claim_id,
                source=source,
                target=target,
                attribute=attribute,
                value=claim.get("value"),
                proof=proof,
                expected=expected_payload,
                evidence=evidence_payload,
            )
        )

    return IdentityFlow(nodes=nodes, claims=claims)


def audit_identity_flow(flow: IdentityFlow) -> IdentityFlowReport:
    """Analyse *flow* for contradictions, mismatches, and unverifiable claims."""

    contradictions: list[str] = []
    mismatches: list[str] = []
    unverifiable: list[str] = []

    attribute_map: Dict[tuple[str, str], Dict[str, dict[str, Any]]] = {}

    for claim in flow.claims:
        # Track contradictory values across claims referencing the same attribute.
        key = (claim.target, claim.attribute)
        canonical_value = _canonicalise_value(claim.value)
        bucket = attribute_map.setdefault(key, {})
        bucket.setdefault(canonical_value, {"value": claim.value, "claims": []})
        bucket[canonical_value]["claims"].append(claim.id)

        # Mismatched nodes or expectations.
        source_node = flow.nodes.get(claim.source)
        target_node = flow.nodes.get(claim.target)
        if source_node is None:
            mismatches.append(
                f"Claim {claim.id} references unknown source identity {claim.source}."
            )
        if target_node is None:
            mismatches.append(
                f"Claim {claim.id} references unknown target identity {claim.target}."
            )
        else:
            for attribute_name, expected_value in claim.expected.items():
                actual_value = target_node.attributes.get(attribute_name)
                if actual_value != expected_value:
                    mismatches.append(
                        "Claim {claim} expected {attr}={expected!r} for {target} "
                        "but observed {actual!r}.".format(
                            claim=claim.id,
                            attr=attribute_name,
                            expected=expected_value,
                            target=claim.target,
                            actual=actual_value,
                        )
                    )

        if not claim.proof:
            unverifiable.append(
                f"Claim {claim.id} ({claim.source}->{claim.target}) is missing proof material."
            )

    for (target, attribute), buckets in attribute_map.items():
        if len(buckets) <= 1:
            continue
        presentations = []
        for entry in buckets.values():
            value_repr = _canonicalise_value(entry["value"])
            claim_ids = ", ".join(sorted(entry["claims"]))
            presentations.append(f"{value_repr} (claims: {claim_ids})")
        contradictions.append(
            f"Conflicting {attribute!r} assertions for {target}: "
            + "; ".join(presentations)
        )

    return IdentityFlowReport(
        nodes_evaluated=flow.node_count,
        claims_evaluated=flow.claim_count,
        contradictions=contradictions,
        mismatches=mismatches,
        unverifiable=unverifiable,
    )


__all__ = [
    "IdentityClaim",
    "IdentityFlow",
    "IdentityFlowReport",
    "IdentityNode",
    "audit_identity_flow",
    "load_identity_flow",
]

