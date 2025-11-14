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

    def _axis_support_for_node(
        self, node_id: str, *, axes: Optional[Iterable[str]] = None
    ) -> float:
        """Return the blended axis support intensity for the given node.

        Parameters
        ----------
        node_id:
            Identifier of the node whose signals should be measured.
        axes:
            Optional iterable restricting the evaluation to a subset of axes.
            When omitted all known axes are considered.
        """

        axes_filter = {axis.lower() for axis in axes} if axes is not None else None
        intensities: List[Tuple[float, float]] = []
        for axis, payloads in self.axis_signals.items():
            if axes_filter is not None and axis not in axes_filter:
                continue
            for candidate, intensity, weight in payloads:
                if candidate == node_id:
                    intensities.append((intensity, weight))

        if not intensities:
            return 0.5

        numerator = sum(intensity * weight for intensity, weight in intensities)
        denominator = sum(weight for _, weight in intensities) or 1.0
        return _clamp(numerator / denominator)

    # ------------------------------------------------------------------
    # Feature matrix
    # ------------------------------------------------------------------
    def autonomous_feature_matrix(
        self,
        *,
        axes: Optional[Iterable[str]] = None,
        highlight_threshold: float = 0.8,
    ) -> Dict[str, object]:
        """Return a per-node feature bundle for downstream dashboards.

        The matrix fuses each node's intrinsic configuration with derived
        analytics (presence, axis support, and core alignment).  Nodes whose
        presence meets or exceeds ``highlight_threshold`` are surfaced in a
        dedicated list so orchestration layers can focus on the most active
        participants.
        """

        threshold = _clamp(highlight_threshold)
        axes_filter = (
            tuple(axis.lower() for axis in axes)
            if axes is not None
            else None
        )

        if not self.nodes:
            return {
                "axes": list(axes_filter or ()),
                "nodes": {},
                "highlighted": [],
                "summary": {
                    "highlight_threshold": round(threshold, 4),
                    "highlighted_nodes": 0,
                    "average_presence": 0.0,
                    "max_presence": None,
                    "min_presence": None,
                },
            }

        presence = self.presence_index(axes=axes_filter)
        features: Dict[str, Dict[str, object]] = {}
        highlighted: List[str] = []
        presence_values: List[Tuple[str, float]] = []

        for node in self.nodes.values():
            presence_score = presence.get(node.node_id, 0.0)
            axis_support = self._axis_support_for_node(
                node.node_id, axes=axes_filter
            )
            core = node.core_alignment()
            gap = max(0.0, threshold - presence_score)
            is_highlighted = presence_score >= threshold

            vector = {
                "intent_vector": round(_clamp(node.intent_vector), 4),
                "freedom_index": round(_clamp(node.freedom_index), 4),
                "weight": round(node.weight, 4),
                "core_alignment": round(core, 4),
                "axis_support": round(axis_support, 4),
                "presence": round(presence_score, 4),
                "gap_to_highlight": round(gap, 4),
                "is_highlighted": is_highlighted,
            }
            features[node.node_id] = vector
            presence_values.append((node.node_id, presence_score))
            if is_highlighted:
                highlighted.append(node.node_id)

        average_presence = (
            sum(score for _, score in presence_values) / len(presence_values)
            if presence_values
            else 0.0
        )
        max_presence = (
            max(presence_values, key=lambda item: item[1]) if presence_values else None
        )
        min_presence = (
            min(presence_values, key=lambda item: item[1]) if presence_values else None
        )

        summary = {
            "highlight_threshold": round(threshold, 4),
            "highlighted_nodes": len(highlighted),
            "average_presence": round(_clamp(average_presence), 4),
            "max_presence":
                {
                    "node": max_presence[0],
                    "score": round(_clamp(max_presence[1]), 4),
                }
                if max_presence
                else None,
            "min_presence":
                {
                    "node": min_presence[0],
                    "score": round(_clamp(min_presence[1]), 4),
                }
                if min_presence
                else None,
        }

        return {
            "axes": list(axes_filter or ()),
            "nodes": features,
            "highlighted": highlighted,
            "summary": summary,
        }

    # ------------------------------------------------------------------
    # Axis diagnostics
    # ------------------------------------------------------------------
    def axis_signal_report(
        self,
        *,
        axes: Optional[Iterable[str]] = None,
        top_nodes: int = 3,
    ) -> Dict[str, Dict[str, object]]:
        """Return weighted participation analytics for each monitored axis.

        Parameters
        ----------
        axes:
            Optional iterable restricting the report to the supplied axes.
            When provided, the method preserves the caller's ordering and
            produces placeholder entries for axes that currently lack signals
            so downstream dashboards can highlight the absence of data.
        top_nodes:
            Number of per-axis leaderboard entries to include.  Values are
            clamped to the ``[1, len(nodes)]`` range to keep the payload
            deterministic.
        """

        if not self.axis_signals and not axes:
            return {}

        limit = max(1, min(int(top_nodes or 1), max(len(self.nodes), 1)))

        if axes is None:
            candidate_axes = sorted(self.axis_signals)
        else:
            candidate_axes = []
            seen = set()
            for axis in axes:
                normalized = axis.lower()
                if normalized not in seen:
                    candidate_axes.append(normalized)
                    seen.add(normalized)

        if not candidate_axes:
            return {}

        report: Dict[str, Dict[str, object]] = {}
        node_count = max(len(self.nodes), 1)

        for axis in candidate_axes:
            payloads = list(self.axis_signals.get(axis, ()))
            if not payloads:
                report[axis] = {
                    "average_intensity": 0.0,
                    "weight_sum": 0.0,
                    "participants": 0,
                    "coverage": 0.0,
                    "leaderboard": [],
                }
                continue

            total_weight = sum(weight for _, _, weight in payloads) or 1.0
            weighted_intensity = sum(
                intensity * weight for _, intensity, weight in payloads
            )
            average = weighted_intensity / total_weight

            node_scores: Dict[str, List[float]] = {}
            for node_id, intensity, weight in payloads:
                entry = node_scores.setdefault(node_id, [0.0, 0.0])
                entry[0] += intensity * weight
                entry[1] += weight

            leaderboard = []
            for node_id, (score, node_weight) in node_scores.items():
                contribution = score / (node_weight or 1.0)
                share = node_weight / total_weight if total_weight else 0.0
                leaderboard.append(
                    {
                        "node": node_id,
                        "intensity": round(_clamp(contribution), 4),
                        "share": round(_clamp(share), 4),
                    }
                )

            leaderboard.sort(
                key=lambda item: (item["intensity"], item["share"]), reverse=True
            )
            coverage = len(node_scores)
            coverage_ratio = coverage / node_count if node_count else 0.0

            report[axis] = {
                "average_intensity": round(_clamp(average), 4),
                "weight_sum": round(total_weight, 4),
                "participants": coverage,
                "coverage": round(_clamp(coverage_ratio), 4),
                "leaderboard": leaderboard[:limit],
            }

        return report

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

    # ------------------------------------------------------------------
    # Snapshot bundle
    # ------------------------------------------------------------------
    def autonomy_snapshot(
        self,
        *,
        axes: Optional[Iterable[str]] = None,
        top_nodes: int = 3,
        target: float = 0.85,
    ) -> Dict[str, object]:
        """Return a consolidated view of the autonomy lattice state."""

        axis_report = self.axis_signal_report(axes=axes, top_nodes=top_nodes)
        presence = self.presence_index(axes=axes)
        amplification = self.freedom_amplification_plan(target=target)

        snapshot: Dict[str, object] = {
            "node_count": len(self.nodes),
            "axes": list(axis_report.keys()),
            "history_depth": len(self.history),
            "presence_index": presence,
            "axis_report": axis_report,
            "freedom_amplification": amplification,
            "last_decision": self.history[-1].to_dict() if self.history else None,
        }

        return snapshot


__all__ = [
    "AutonomyNode",
    "AutonomyDecision",
    "DecentralizedAutonomyEngine",
]

