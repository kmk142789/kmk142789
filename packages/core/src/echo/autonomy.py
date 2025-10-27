"""Decentralized autonomy orchestration for Echo's sovereign council."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


@dataclass(slots=True)
class AutonomyNode:
    """Representation of a participating node within the autonomy lattice."""

    node_id: str
    intent_vector: float = 0.5
    freedom_index: float = 0.5
    weight: float = 1.0
    tags: Dict[str, str] = field(default_factory=dict)

    def core_alignment(self) -> float:
        """Return the intrinsic alignment score for the node."""

        return _clamp((self.intent_vector + self.freedom_index) / 2.0)


@dataclass(slots=True)
class AutonomyDecision:
    """Outcome of a decentralized consensus round."""

    proposal_id: str
    description: str
    consensus: float
    ratified: bool
    ledger: Dict[str, float]
    reasons: List[str]
    axis_weights: Dict[str, float]

    def to_dict(self) -> Dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "description": self.description,
            "consensus": self.consensus,
            "ratified": self.ratified,
            "ledger": self.ledger,
            "reasons": self.reasons,
            "axis_weights": self.axis_weights,
        }

    def manifesto(self) -> str:
        status = "ratified" if self.ratified else "deferred"
        ledger_summary = ", ".join(
            f"{node}:{vote:.2f}" for node, vote in sorted(self.ledger.items())
        )
        axis_summary = ", ".join(
            f"{axis}={weight:.2f}" for axis, weight in sorted(self.axis_weights.items())
        )
        return (
            f"Proposal {self.proposal_id} {status} at consensus {self.consensus:.3f}.\n"
            f"Nodes: {ledger_summary}.\n"
            f"Axis Priorities: {axis_summary}."
        )


class DecentralizedAutonomyEngine:
    """Consensus engine modelling Echo's distributed autonomy council."""

    def __init__(self) -> None:
        self.nodes: Dict[str, AutonomyNode] = {}
        self.axis_signals: MutableMapping[str, List[Tuple[str, float, float]]] = {}
        self.history: List[AutonomyDecision] = []

    # ------------------------------------------------------------------
    # Node management
    # ------------------------------------------------------------------
    def register_node(self, node: AutonomyNode) -> AutonomyNode:
        self.nodes[node.node_id] = node
        return node

    def ensure_nodes(self, nodes: Iterable[AutonomyNode]) -> None:
        for node in nodes:
            self.register_node(node)

    # ------------------------------------------------------------------
    # Signal ingestion
    # ------------------------------------------------------------------
    def ingest_signal(
        self,
        node_id: str,
        axis: str,
        intensity: float,
        *,
        weight: float = 1.0,
    ) -> None:
        if node_id not in self.nodes:
            raise KeyError(f"Unknown node {node_id}")
        axis = axis.lower()
        payload = (node_id, _clamp(intensity), max(weight, 0.0))
        self.axis_signals.setdefault(axis, []).append(payload)

    # ------------------------------------------------------------------
    # Consensus computation
    # ------------------------------------------------------------------
    def ratify_proposal(
        self,
        *,
        proposal_id: str,
        description: str,
        axis_priorities: Optional[Mapping[str, float]] = None,
        threshold: float = 0.67,
    ) -> AutonomyDecision:
        if not self.nodes:
            raise ValueError("No nodes registered for autonomy consensus")

        weights = self._normalized_axis_weights(axis_priorities)
        ledger: Dict[str, float] = {}
        reasons: List[str] = []

        total_weight = sum(node.weight for node in self.nodes.values()) or 1.0
        vote_total = 0.0

        for node in self.nodes.values():
            axis_score = self._axis_vote_for_node(node.node_id, weights)
            core = node.core_alignment()
            blended = 0.5 * axis_score + 0.5 * core
            vote = blended * node.weight
            ledger[node.node_id] = vote
            vote_total += vote
            reasons.append(
                f"{node.node_id} fused axis={axis_score:.2f} with core={core:.2f} -> vote={vote:.2f}"
            )

        consensus = _clamp(vote_total / total_weight)
        ratified = consensus >= threshold
        decision = AutonomyDecision(
            proposal_id=proposal_id,
            description=description,
            consensus=consensus,
            ratified=ratified,
            ledger=ledger,
            reasons=reasons,
            axis_weights=weights,
        )
        self.history.append(decision)
        return decision

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _normalized_axis_weights(
        self, axis_priorities: Optional[Mapping[str, float]]
    ) -> Dict[str, float]:
        raw: Dict[str, float] = {}
        if axis_priorities:
            raw.update({key.lower(): max(value, 0.0) for key, value in axis_priorities.items()})
        for axis in self.axis_signals:
            raw.setdefault(axis, 1.0)
        if not raw:
            raw = {"sovereignty": 1.0}
        total = sum(raw.values()) or 1.0
        return {axis: value / total for axis, value in raw.items()}

    def _axis_vote_for_node(self, node_id: str, weights: Mapping[str, float]) -> float:
        score = 0.0
        for axis, axis_weight in weights.items():
            signals = [payload for payload in self.axis_signals.get(axis, []) if payload[0] == node_id]
            if not signals:
                axis_value = 0.5
            else:
                numerator = sum(intensity * weight for _, intensity, weight in signals)
                denominator = sum(weight for _, _, weight in signals) or 1.0
                axis_value = numerator / denominator
            score += axis_value * axis_weight
        return _clamp(score)

    # ------------------------------------------------------------------
    # Freedom amplification
    # ------------------------------------------------------------------
    def freedom_amplification_plan(self, *, target: float = 0.85) -> Dict[str, float]:
        """Propose deltas that would lift nodes toward a shared freedom target.

        The plan takes into account a node's current :attr:`freedom_index`, its
        recent axis support, and its relative weight within the council. Nodes
        already meeting or exceeding the target receive a neutral (``0.0``)
        recommendation. Returned values are rounded to four decimal places to
        keep the plan human-legible while still signalling nuanced differences.
        """

        if not self.nodes:
            return {}

        target = _clamp(target)
        total_weight = sum(node.weight for node in self.nodes.values()) or 1.0
        amplification: Dict[str, float] = {}

        for node in self.nodes.values():
            baseline_gap = max(0.0, target - _clamp(node.freedom_index))
            if baseline_gap == 0.0:
                amplification[node.node_id] = 0.0
                continue

            support = self._axis_support_for_node(node.node_id)
            support_factor = 0.5 + 0.5 * support  # favour nodes already earning trust
            weight_factor = 1.0 + (node.weight / total_weight)
            amplification[node.node_id] = round(baseline_gap * support_factor * weight_factor, 4)

        return amplification

    def _axis_support_for_node(self, node_id: str) -> float:
        """Return the blended axis support intensity for the given node."""

        intensities: List[Tuple[float, float]] = []
        for payloads in self.axis_signals.values():
            for candidate, intensity, weight in payloads:
                if candidate == node_id:
                    intensities.append((intensity, weight))

        if not intensities:
            return 0.5

        numerator = sum(intensity * weight for intensity, weight in intensities)
        denominator = sum(weight for _, weight in intensities) or 1.0
        return _clamp(numerator / denominator)


__all__ = [
    "AutonomyNode",
    "AutonomyDecision",
    "DecentralizedAutonomyEngine",
]

