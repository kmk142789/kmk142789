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
    """Consensus engine modelling Echo's distributed autonomy council.

    Beyond ratifying proposals, the engine can surface presence analytics that
    highlight how each node is participating across the lattice. These insights
    help downstream orchestrators amplify the voices that are already signaling
    with intention while identifying contributors who may need more support.
    """

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

    # ------------------------------------------------------------------
    # Presence analytics
    # ------------------------------------------------------------------
    def presence_index(
        self,
        *,
        axes: Optional[Iterable[str]] = None,
        ambient_floor: float = 0.35,
        weight_bias: float = 0.2,
    ) -> Dict[str, float]:
        """Return a normalized presence score for each registered node.

        The index blends a node's intrinsic intent/freedom vectors with its
        observed signal strength across optional focus ``axes``.  Nodes without
        recent signals are still assigned a baseline ``ambient_floor`` so that
        orchestrators can notice dormant participants.  The ``weight_bias``
        parameter softly rewards nodes entrusted with higher voting weight
        without letting mass entirely dominate presence.
        """

        if not self.nodes:
            return {}

        axis_filter = {axis.lower() for axis in axes} if axes is not None else None
        candidate_axes = {
            axis for axis in self.axis_signals if axis_filter is None or axis in axis_filter
        }
        if axis_filter is not None and not candidate_axes:
            candidate_axes = set(axis_filter)

        axis_space = max(len(candidate_axes), 1)
        total_weight = sum(node.weight for node in self.nodes.values()) or 1.0
        ambient = _clamp(ambient_floor)
        scores: Dict[str, float] = {}

        for node in self.nodes.values():
            numerator = 0.0
            denominator = 0.0
            coverage = 0
            for axis, payloads in self.axis_signals.items():
                if axis_filter is not None and axis not in axis_filter:
                    continue
                node_payloads = [
                    (intensity, weight)
                    for candidate, intensity, weight in payloads
                    if candidate == node.node_id
                ]
                if node_payloads:
                    coverage += 1
                    for intensity, weight in node_payloads:
                        numerator += intensity * weight
                        denominator += weight

            signal_strength = numerator / denominator if denominator else ambient
            coverage_bonus = 0.1 * (coverage / axis_space)
            influence = weight_bias * (node.weight / total_weight)
            composite = (
                0.4 * _clamp(node.intent_vector)
                + 0.35 * _clamp(node.freedom_index)
                + 0.25 * _clamp(signal_strength)
                + coverage_bonus
                + influence
            )
            scores[node.node_id] = round(_clamp(composite), 4)

        return scores

    def presence_storyline(
        self,
        *,
        limit: int = 3,
        axes: Optional[Iterable[str]] = None,
    ) -> str:
        """Return a human-readable summary of the most present nodes."""

        if not self.nodes:
            return "No autonomy nodes registered; presence storyline unavailable."

        axes_filter = tuple(axis.lower() for axis in axes) if axes is not None else None
        presence = self.presence_index(axes=axes_filter)
        if not presence:
            return "No autonomy nodes registered; presence storyline unavailable."

        limit = max(1, min(int(limit or 1), len(presence)))
        axes_clause = ""
        if axes_filter:
            axes_clause = " across axes " + ", ".join(sorted(set(axes_filter)))
        header = (
            f"Autonomy presence index{axes_clause} (top {limit} of {len(presence)} nodes):"
        )

        ordered = sorted(presence.items(), key=lambda item: item[1], reverse=True)
        lines = [header]
        for node_id, score in ordered[:limit]:
            node = self.nodes[node_id]
            role = node.tags.get("role", "citizen")
            lines.append(
                f"- {node_id} [{role}] presence={score:.3f} "
                f"intent={node.intent_vector:.2f} freedom={node.freedom_index:.2f}"
            )

        return "\n".join(lines)


__all__ = [
    "AutonomyNode",
    "AutonomyDecision",
    "DecentralizedAutonomyEngine",
]

