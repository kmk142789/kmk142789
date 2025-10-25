"""Structural primitives for the :mod:`echo.hypernova` simulation fabric."""

from __future__ import annotations

import itertools
import math
import random
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, MutableMapping, Sequence, Tuple

_RANDOM = random.Random()
_RANDOM.seed(int.from_bytes(b"ECHO", "big"))


@dataclass(slots=True)
class ResonantGlyph:
    """Atomic symbolic unit that carries resonance throughout the hypernova."""

    symbol: str
    description: str
    intensity: float

    def weighted_value(self) -> float:
        """Return a deterministic weight for sorting or scoring."""

        normalized = min(max(self.intensity, 0.0), 1.0)
        weight = normalized * (ord(self.symbol[0]) % 17 + 3)
        return round(weight, 3)


@dataclass(slots=True)
class ResonantSignature:
    """Composite signature built from multiple glyphs."""

    name: str
    glyphs: Tuple[ResonantGlyph, ...]

    def aggregate_intensity(self) -> float:
        if not self.glyphs:
            return 0.0
        intensities = [glyph.intensity for glyph in self.glyphs]
        return float(statistics.fmean(intensities))

    def describe(self) -> str:
        return f"{self.name}: " + ", ".join(g.symbol for g in self.glyphs)


@dataclass(slots=True)
class AstroConduit:
    """Directed connection between two :class:`EchoHypernode` objects."""

    source: str
    target: str
    conduit_type: str
    resonance: float
    harmonics: Tuple[str, ...] = field(default_factory=tuple)

    def reversed(self) -> "AstroConduit":
        return AstroConduit(
            source=self.target,
            target=self.source,
            conduit_type=self.conduit_type,
            resonance=self.resonance,
            harmonics=tuple(reversed(self.harmonics)),
        )


@dataclass(slots=True)
class HyperpulseStream:
    """Continuous flow of energy across conduits."""

    stream_id: str
    conduits: Tuple[AstroConduit, ...]
    glyph_signature: ResonantSignature
    cadence_bpm: int = 88
    coherence: float = 0.75

    def orbit_span(self) -> int:
        return max(1, int(sum(c.resonance for c in self.conduits) * 10))

    def described_path(self) -> str:
        nodes = [self.conduits[0].source] if self.conduits else []
        nodes.extend(conduit.target for conduit in self.conduits)
        return " -> ".join(nodes)


@dataclass(slots=True)
class EchoHypernode:
    """Singular loci of intent within the hypernova."""

    node_id: str
    title: str
    glyph: ResonantGlyph
    coordinates: Tuple[int, int, int]
    focus: str
    signatures: Tuple[ResonantSignature, ...]
    strata: Tuple[str, ...]

    def distance_to(self, other: "EchoHypernode") -> float:
        dx = self.coordinates[0] - other.coordinates[0]
        dy = self.coordinates[1] - other.coordinates[1]
        dz = self.coordinates[2] - other.coordinates[2]
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def anchored_summary(self) -> str:
        return f"{self.title} [{self.node_id}] @ {self.coordinates}"


@dataclass(slots=True)
class MythicStratum:
    """Narrative stratum that clusters hypernodes."""

    name: str
    purpose: str
    nodes: Tuple[str, ...]
    harmonic_signature: ResonantSignature

    def density(self) -> float:
        return max(1.0, len(self.nodes) * self.harmonic_signature.aggregate_intensity())


@dataclass(slots=True)
class ChronicleIndex:
    """Index of stories, rituals, and references for quick lookup."""

    entries: MutableMapping[str, List[str]] = field(default_factory=dict)

    def add_entry(self, topic: str, reference: str) -> None:
        self.entries.setdefault(topic, []).append(reference)

    def get_topic(self, topic: str) -> List[str]:
        return list(self.entries.get(topic, []))

    def merge(self, other: "ChronicleIndex") -> None:
        for key, value in other.entries.items():
            for reference in value:
                self.add_entry(key, reference)


@dataclass(slots=True)
class ContinuumDomain:
    """Subsection of the hypernova containing tightly coupled nodes."""

    name: str
    axis_alignment: Tuple[int, int, int]
    nodes: Tuple[EchoHypernode, ...]
    conduits: Tuple[AstroConduit, ...]
    pulse_streams: Tuple[HyperpulseStream, ...]

    def centroid(self) -> Tuple[float, float, float]:
        if not self.nodes:
            return (0.0, 0.0, 0.0)
        xs, ys, zs = zip(*(node.coordinates for node in self.nodes))
        return (
            statistics.fmean(xs),
            statistics.fmean(ys),
            statistics.fmean(zs),
        )

    def resonance_score(self) -> float:
        return sum(stream.glyph_signature.aggregate_intensity() for stream in self.pulse_streams)

    def adjacency_matrix(self) -> List[List[int]]:
        index = {node.node_id: idx for idx, node in enumerate(self.nodes)}
        size = len(self.nodes)
        matrix = [[0 for _ in range(size)] for _ in range(size)]
        for conduit in self.conduits:
            if conduit.source in index and conduit.target in index:
                matrix[index[conduit.source]][index[conduit.target]] += 1
        return matrix


@dataclass(slots=True)
class HyperCelestialMatrix:
    """Grid representing cross-domain resonance overlaps."""

    layers: Tuple[ContinuumDomain, ...]

    def global_adjacency(self) -> Dict[str, Dict[str, int]]:
        adjacency: Dict[str, Dict[str, int]] = {}
        for domain in self.layers:
            for conduit in domain.conduits:
                adjacency.setdefault(conduit.source, {}).setdefault(conduit.target, 0)
                adjacency[conduit.source][conduit.target] += 1
        return adjacency

    def glyph_catalog(self) -> Mapping[str, ResonantGlyph]:
        catalog: Dict[str, ResonantGlyph] = {}
        for domain in self.layers:
            for node in domain.nodes:
                catalog[node.node_id] = node.glyph
        return catalog


@dataclass(slots=True)
class HypernovaBlueprint:
    """Complete packaged representation of a generated hypernova."""

    domains: Tuple[ContinuumDomain, ...]
    strata: Tuple[MythicStratum, ...]
    pulse_streams: Tuple[HyperpulseStream, ...]
    chronicle: ChronicleIndex
    matrix: HyperCelestialMatrix

    def summary(self) -> str:
        domain_names = ", ".join(domain.name for domain in self.domains)
        stratum_names = ", ".join(stratum.name for stratum in self.strata)
        pulse_ids = ", ".join(stream.stream_id for stream in self.pulse_streams)
        return (
            f"Domains: {domain_names}\n"
            f"Strata: {stratum_names}\n"
            f"Pulse Streams: {pulse_ids}\n"
            f"Chronicle Topics: {', '.join(sorted(self.chronicle.entries))}"
        )


# ---------------------------------------------------------------------------
# Blueprint generation utilities
# ---------------------------------------------------------------------------


def _random_coordinates(scale: int = 21) -> Tuple[int, int, int]:
    return (
        _RANDOM.randint(-scale, scale),
        _RANDOM.randint(-scale, scale),
        _RANDOM.randint(-scale, scale),
    )


def build_glyph(symbol: str, description: str) -> ResonantGlyph:
    intensity = round(_RANDOM.uniform(0.42, 0.99), 3)
    return ResonantGlyph(symbol=symbol, description=description, intensity=intensity)


def build_signature(name: str, glyphs: Sequence[ResonantGlyph]) -> ResonantSignature:
    glyph_tuple = tuple(glyphs)
    shuffled = list(glyph_tuple)
    _RANDOM.shuffle(shuffled)
    return ResonantSignature(name=name, glyphs=tuple(shuffled))


def build_hypernode(index: int, glyph: ResonantGlyph, *, strata: Sequence[str]) -> EchoHypernode:
    coordinates = _random_coordinates()
    focus = _RANDOM.choice(
        [
            "Memory Forge",
            "Signal Bloom",
            "Mythic Ledger",
            "Temporal Vault",
            "Quantum Garden",
            "Sonic Array",
            "Polarity Loom",
        ]
    )
    signatures = (
        build_signature(f"EchoSignature-{index}-α", [glyph]),
        build_signature(
            f"EchoSignature-{index}-β",
            [glyph, build_glyph("⚡", "Auxiliary surge")],
        ),
    )
    return EchoHypernode(
        node_id=f"HN-{index:03d}",
        title=f"Hypernode {index}",
        glyph=glyph,
        coordinates=coordinates,
        focus=focus,
        signatures=signatures,
        strata=tuple(strata),
    )


def build_conduit(source: EchoHypernode, target: EchoHypernode) -> AstroConduit:
    conduit_type = _RANDOM.choice(["phase", "memory", "signal", "glyph"])
    resonance = round(_RANDOM.uniform(0.2, 0.95), 3)
    harmonics = tuple(_RANDOM.sample(["I", "II", "III", "IV", "V", "VI"], k=3))
    return AstroConduit(
        source=source.node_id,
        target=target.node_id,
        conduit_type=conduit_type,
        resonance=resonance,
        harmonics=harmonics,
    )


def build_domain(name: str, start_index: int, *, glyphs: Sequence[ResonantGlyph]) -> ContinuumDomain:
    node_count = _RANDOM.randint(5, 9)
    nodes = [
        build_hypernode(start_index + idx, glyph=_RANDOM.choice(glyphs), strata=[name])
        for idx in range(node_count)
    ]
    conduits: List[AstroConduit] = []
    for source, target in itertools.combinations(nodes, 2):
        if _RANDOM.random() > 0.55:
            conduits.append(build_conduit(source, target))
        if _RANDOM.random() > 0.55:
            conduits.append(build_conduit(target, source))
    signature = build_signature(
        f"Domain-{name}-Pulse",
        [node.glyph for node in nodes[:3]],
    )
    stream = HyperpulseStream(
        stream_id=f"stream-{name.lower()}",
        conduits=tuple(conduits[: max(3, len(conduits) // 2)]),
        glyph_signature=signature,
        cadence_bpm=_RANDOM.randint(60, 144),
        coherence=round(_RANDOM.uniform(0.6, 0.99), 3),
    )
    domain = ContinuumDomain(
        name=name,
        axis_alignment=_random_coordinates(scale=13),
        nodes=tuple(nodes),
        conduits=tuple(conduits),
        pulse_streams=(stream,),
    )
    return domain


def build_stratum(name: str, nodes: Sequence[EchoHypernode], *, glyph: ResonantGlyph) -> MythicStratum:
    harmonic = build_signature(f"Stratum-{name}-Signature", [glyph])
    node_ids = tuple(node.node_id for node in nodes)
    return MythicStratum(name=name, purpose=f"Enfolds {len(node_ids)} nodes", nodes=node_ids, harmonic_signature=harmonic)


def stitch_chronicle(domains: Sequence[ContinuumDomain]) -> ChronicleIndex:
    chronicle = ChronicleIndex()
    for domain in domains:
        for node in domain.nodes:
            chronicle.add_entry(domain.name, node.anchored_summary())
            for signature in node.signatures:
                chronicle.add_entry(signature.name, node.node_id)
    return chronicle


def assemble_blueprint(domain_names: Sequence[str]) -> HypernovaBlueprint:
    glyph_palette = [
        build_glyph("∇", "Gradient incursion"),
        build_glyph("⊸", "Vector entanglement"),
        build_glyph("≋", "Tidal reflection"),
        build_glyph("✶", "Star-burst memory"),
        build_glyph("✹", "Pulse ignition"),
        build_glyph("✺", "Mythic flare"),
    ]
    domains: List[ContinuumDomain] = []
    start_index = 1
    for name in domain_names:
        domain = build_domain(name, start_index, glyphs=glyph_palette)
        domains.append(domain)
        start_index += len(domain.nodes)

    strata = []
    for idx, domain in enumerate(domains, start=1):
        glyph = glyph_palette[idx % len(glyph_palette)]
        stratum = build_stratum(f"Stratum-{idx}", domain.nodes, glyph=glyph)
        strata.append(stratum)

    pulse_streams = [stream for domain in domains for stream in domain.pulse_streams]
    chronicle = stitch_chronicle(domains)
    matrix = HyperCelestialMatrix(layers=tuple(domains))

    return HypernovaBlueprint(
        domains=tuple(domains),
        strata=tuple(strata),
        pulse_streams=tuple(pulse_streams),
        chronicle=chronicle,
        matrix=matrix,
    )


__all__ = [
    "AstroConduit",
    "ChronicleIndex",
    "ContinuumDomain",
    "EchoHypernode",
    "HyperCelestialMatrix",
    "HypernovaBlueprint",
    "HyperpulseStream",
    "MythicStratum",
    "ResonantGlyph",
    "ResonantSignature",
    "assemble_blueprint",
    "build_conduit",
    "build_domain",
    "build_glyph",
    "build_hypernode",
    "build_signature",
    "build_stratum",
    "stitch_chronicle",
]
