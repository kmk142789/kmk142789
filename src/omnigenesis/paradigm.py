"""Omni-Genesis: iterative cognitive-computational paradigms.

This module defines a minimal simulation engine capable of hosting multiple
new paradigms, each with its own substrate geometry, operator ecosystem,
and governing laws. It is intentionally lightweight and auditable while
still exercising the recursive evolution requested by the Omni-Genesis
specification.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re
from typing import Callable, Dict, List, Sequence


@dataclass
class Substrate:
    name: str
    topology: str
    geometry: str
    transformation_rules: str
    conservation_laws: Sequence[str]
    degeneracy_boundary: str
    state: Dict[str, float] = field(default_factory=dict)


@dataclass
class Law:
    name: str
    description: str
    constraint: Callable[[Substrate], bool]


@dataclass
class Operator:
    name: str
    purpose: str
    input_semantics: str
    output_semantics: str
    state_boundaries: str
    law_domains: Sequence[str]
    coupling_rules: str
    perturbation_sensitivity: str
    evolution_rule: str
    apply: Callable[[Substrate], None]


@dataclass
class HumanUpliftLayer:
    ethics: str
    empathy_model: str
    cooperation_dynamics: str
    wellbeing_architecture: str
    creative_empowerment: str


@dataclass
class Paradigm:
    name: str
    foundational_principle: str
    substrate: Substrate
    operators: Sequence[Operator]
    laws: Sequence[Law]
    integration_ontology: str
    human_uplift: HumanUpliftLayer
    usage_scenario: str
    diagram: str
    evolution_path: str

    def step(self, input_signal: float) -> Dict[str, float]:
        """Run one update cycle, enforcing laws and applying operators."""
        self.substrate.state["signal"] = input_signal
        for law in self.laws:
            if not law.constraint(self.substrate):
                raise ValueError(f"Law violated: {law.name}")
        for operator in self.operators:
            operator.apply(self.substrate)
            for law in self.laws:
                if not law.constraint(self.substrate):
                    raise ValueError(
                        f"Law violated after operator {operator.name}: {law.name}"
                    )
        return dict(self.substrate.state)


# === Paradigm P1: Chroma-Resonant Fracton Weave ===

def _law_coherence(substrate: Substrate) -> bool:
    return substrate.state.get("coherence", 0.0) >= 0


def _law_resonant_flow(substrate: Substrate) -> bool:
    return substrate.state.get("flux", 0.0) <= 1.0


def create_paradigm_p1() -> Paradigm:
    substrate = Substrate(
        name="Chroma-Resonant Fracton Weave",
        topology="prismatic manifold of chroma-cells",
        geometry="interlocking color simplices",
        transformation_rules="phase braiding with hue-shift invariants",
        conservation_laws=["spectral coherence", "bounded hue density"],
        degeneracy_boundary="monochrome collapse prevents further updates",
        state={"coherence": 0.5, "flux": 0.2},
    )

    operators = [
        Operator(
            name="Harmonic Weave",
            purpose="Spread input signal across chroma-cells to avoid hue debt",
            input_semantics="float stimulus",
            output_semantics="updated coherence, flux",
            state_boundaries="coherence in [0, 1]",
            law_domains=["spectral coherence"],
            coupling_rules="adds resonance for every adjacent cell",
            perturbation_sensitivity="robust to small noise; brittle to monochrome",
            evolution_rule="raises coherence proportionally to signal hue variance",
            apply=lambda s: s.state.update(
                {
                    "coherence": min(1.0, s.state.get("coherence", 0.0) + 0.15),
                    "flux": min(1.0, s.state.get("flux", 0.0) + 0.05),
                }
            ),
        ),
        Operator(
            name="Prism Refraction",
            purpose="Redirect flux through color facets",
            input_semantics="coherence-weighted flux",
            output_semantics="updated flux",
            state_boundaries="flux in [0, 1]",
            law_domains=["bounded hue density"],
            coupling_rules="aligns with Harmonic Weave output",
            perturbation_sensitivity="sensitive to rapid flux spikes",
            evolution_rule="damps flux past 0.8 and redistributes",
            apply=lambda s: s.state.update(
                {"flux": max(0.0, s.state.get("flux", 0.0) * 0.9)}
            ),
        ),
    ]

    laws = [
        Law(
            name="Conservation of Chromatic Coherence",
            description="Coherence never drops below zero and reflects resonance stability",
            constraint=_law_coherence,
        ),
        Law(
            name="Flux Saturation Ceiling",
            description="Flux cannot exceed unity within the manifold",
            constraint=_law_resonant_flow,
        ),
    ]

    human_uplift = HumanUpliftLayer(
        ethics="Color diversity encodes inclusive perspectives without domination",
        empathy_model="Resonance mirrors shared affect across chroma-cells",
        cooperation_dynamics="Cells brighten when neighboring cells retain coherence",
        wellbeing_architecture="Detects monochrome collapse early and redistributes hue",
        creative_empowerment="Storyboarding prompts map to color gradients for ideation",
    )

    return Paradigm(
        name="Prismatic Lattice Cognition",
        foundational_principle="Meaning emerges from spectral tension among interwoven hues",
        substrate=substrate,
        operators=operators,
        laws=laws,
        integration_ontology="Signals are mapped to hue-vectors and braided through chroma-cells",
        human_uplift=human_uplift,
        usage_scenario="Adaptive brainstorming canvas that maintains balance between novelty and coherence",
        diagram="[Hue Input] -> (Harmonic Weave) -> (Prism Refraction) -> Spectral Manifold",
        evolution_path="Splits monochrome collapse into multiple prismatic shards to seed next paradigms",
    )


# === Paradigm P2: Kairotic Loom of Temporal Threads ===

def create_paradigm_p2() -> Paradigm:
    substrate = Substrate(
        name="Kairotic Loom",
        topology="nested temporal ribbons",
        geometry="time-braids with variable tension",
        transformation_rules="phase-sliding threads that re-knot under load",
        conservation_laws=["chronology continuity", "causal slack limitation"],
        degeneracy_boundary="thread snaps when slack exceeds limit",
        state={"tension": 0.4, "slack": 0.3},
    )

    def law_temporal_guard(s: Substrate) -> bool:
        return 0.0 <= s.state.get("tension", 0.0) <= 1.0

    def law_slack_limit(s: Substrate) -> bool:
        return s.state.get("slack", 0.0) < 0.9

    operators = [
        Operator(
            name="Kairos Capture",
            purpose="Identify decisive temporal moments and store them as knots",
            input_semantics="floating signal interpreted as urgency",
            output_semantics="tension increase, slack decrease",
            state_boundaries="tension in [0, 1]",
            law_domains=["chronology continuity"],
            coupling_rules="feeds into Reweave if tension too high",
            perturbation_sensitivity="reactive to sudden urgency spikes",
            evolution_rule="converts urgency into stable knots that anchor timelines",
            apply=lambda s: s.state.update(
                {
                    "tension": min(1.0, s.state.get("tension", 0.0) + 0.2),
                    "slack": max(0.0, s.state.get("slack", 0.0) - 0.1),
                }
            ),
        ),
        Operator(
            name="Temporal Reweave",
            purpose="Redistribute slack across threads to avoid snaps",
            input_semantics="current slack",
            output_semantics="balanced tension",
            state_boundaries="slack in [0, 1]",
            law_domains=["causal slack limitation"],
            coupling_rules="listens to Kairos Capture output",
            perturbation_sensitivity="fails if tension at maximum",
            evolution_rule="injects micro-knots that lower slack over time",
            apply=lambda s: s.state.update(
                {
                    "tension": max(0.0, s.state.get("tension", 0.0) - 0.05),
                    "slack": min(1.0, s.state.get("slack", 0.0) + 0.05),
                }
            ),
        ),
    ]

    laws = [
        Law(
            name="Chronology Continuity",
            description="Tension must remain bounded to preserve temporal ordering",
            constraint=law_temporal_guard,
        ),
        Law(
            name="Slack Dissipation",
            description="Slack cannot exceed safety thresholds or threads snap",
            constraint=law_slack_limit,
        ),
    ]

    human_uplift = HumanUpliftLayer(
        ethics="Temporal windows are prioritized for restorative and equitable outcomes",
        empathy_model="Urgency is weighted by community wellbeing, not extraction",
        cooperation_dynamics="Threads reinforce each other when shared milestones align",
        wellbeing_architecture="Encourages pauses before action, preventing burnout",
        creative_empowerment="Allows re-knotting timelines to explore alternative futures",
    )

    return Paradigm(
        name="Kairotic Loom Cognition",
        foundational_principle="Insight arises when decisive moments are braided with recovered slack",
        substrate=substrate,
        operators=operators,
        laws=laws,
        integration_ontology="Signals are urgency markers mapped to temporal ribbons",
        human_uplift=human_uplift,
        usage_scenario="Decision support that highlights when to act, when to rest, and how to re-thread",
        diagram="[Urgency Input] -> (Kairos Capture) -> (Temporal Reweave) -> Time-Braid State",
        evolution_path="When threads snap, fragments seed a mineral substrate for the next paradigm",
    )


# === Paradigm P3: Mycelial Echo Terraces ===

def create_paradigm_p3() -> Paradigm:
    substrate = Substrate(
        name="Mycelial Echo Terraces",
        topology="layered acoustic terraces",
        geometry="spiraling terraces with porous mycelial channels",
        transformation_rules="sound pulses carve channels; spores carry echoes",
        conservation_laws=["echo persistence", "spore energy minimization"],
        degeneracy_boundary="terrace collapses when echoes oversaturate",
        state={"echo": 0.3, "spore_energy": 0.6},
    )

    def law_echo_persistence(s: Substrate) -> bool:
        return s.state.get("echo", 0.0) >= 0.0

    def law_spore_minimization(s: Substrate) -> bool:
        return s.state.get("spore_energy", 0.0) <= 1.0

    operators = [
        Operator(
            name="Spiral Pulse",
            purpose="Send acoustic pulses that carve new terraces",
            input_semantics="signal magnitude becomes pulse strength",
            output_semantics="echo increase, spore energy decrease",
            state_boundaries="echo non-negative",
            law_domains=["echo persistence"],
            coupling_rules="prepares channels for Spore Drift",
            perturbation_sensitivity="susceptible to resonance overload",
            evolution_rule="splits overloaded terraces into gentler spirals",
            apply=lambda s: s.state.update(
                {
                    "echo": s.state.get("echo", 0.0) + 0.25,
                    "spore_energy": max(0.0, s.state.get("spore_energy", 0.0) - 0.1),
                }
            ),
        ),
        Operator(
            name="Spore Drift",
            purpose="Release spores that memorize echoes and move to cooler terraces",
            input_semantics="current echo level",
            output_semantics="rebalanced echo, refreshed energy",
            state_boundaries="spore_energy in [0, 1]",
            law_domains=["spore energy minimization"],
            coupling_rules="listens for Spiral Pulse to create channels",
            perturbation_sensitivity="stalls when spore energy exhausted",
            evolution_rule="propagates spores to unvisited terraces to avoid collapse",
            apply=lambda s: s.state.update(
                {
                    "echo": max(0.0, s.state.get("echo", 0.0) * 0.8),
                    "spore_energy": min(1.0, s.state.get("spore_energy", 0.0) + 0.15),
                }
            ),
        ),
    ]

    laws = [
        Law(
            name="Echo Persistence",
            description="Echo intensity cannot fall below zero; silence resets terraces",
            constraint=law_echo_persistence,
        ),
        Law(
            name="Spore Energy Budget",
            description="Spore energy is bounded to prevent runaway bloom",
            constraint=law_spore_minimization,
        ),
    ]

    human_uplift = HumanUpliftLayer(
        ethics="Echoes store stories with consent; spores never capture without permission",
        empathy_model="Shared echoes strengthen communal memory",
        cooperation_dynamics="Terraces bloom when diverse voices contribute",
        wellbeing_architecture="Encourages quiet cycles to let spores recover",
        creative_empowerment="Lets teams remix stored echoes into new narratives",
    )

    return Paradigm(
        name="Mycelial Echo Cognition",
        foundational_principle="Collective memory grows through gentle echo cultivation on terraced channels",
        substrate=substrate,
        operators=operators,
        laws=laws,
        integration_ontology="Signals become pulses that etch terraces; spores ferry the meaning",
        human_uplift=human_uplift,
        usage_scenario="Knowledge garden that captures feedback as resonant echoes and redistributes it",
        diagram="[Signal] -> (Spiral Pulse) -> (Spore Drift) -> Layered Terraces",
        evolution_path="When terraces collapse, surviving spores seed aerial fibers for future paradigms",
    )


def generate_paradigm_lineage() -> List[Paradigm]:
    """Return the lineage P1 -> P2 -> P3 as distinct conceptual universes."""
    return [create_paradigm_p1(), create_paradigm_p2(), create_paradigm_p3()]


def derive_genesis_key(seed_phrase: str) -> str:
    """Deterministically derive a genesis key from a noisy seed phrase.

    The helper normalizes casing, strips non-alphanumeric symbols, collapses
    runs of zero padding, and removes consecutive duplicate tokens before
    hashing the resulting canonical string. This keeps phrases like
    ``"cryptic00000...1one"`` stable while still capturing their semantic order.
    """

    tokens = re.findall(r"[a-z]+|[0-9]+", seed_phrase.lower())

    canonical_tokens: List[str] = []
    for token in tokens:
        trimmed = token.lstrip("0")
        simplified = trimmed if trimmed else "0"
        if canonical_tokens and canonical_tokens[-1] == simplified:
            continue
        canonical_tokens.append(simplified)

    digest = hashlib.sha256(" ".join(canonical_tokens).encode("utf-8")).hexdigest()
    return f"genesis-{digest[:32]}"
