"""Narrative generation layer for the :mod:`echo.hypernova` package."""

from __future__ import annotations

import itertools
import textwrap
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from .architecture import HypernovaBlueprint, HyperpulseStream, MythicStratum


@dataclass(slots=True)
class SagaBeat:
    """Individual narrative beat describing a pivotal moment."""

    title: str
    synopsis: str
    involved_nodes: Sequence[str]
    resonance: float
    glyph_trace: str

    def to_text(self) -> str:
        return textwrap.dedent(
            f"""
            ## {self.title}
            Nodes: {', '.join(self.involved_nodes)}
            Resonance: {self.resonance:.3f}
            Glyph Trace: {self.glyph_trace}

            {self.synopsis}
            """
        ).strip()


class HypernovaSagaBuilder:
    """Construct richly layered story arcs from blueprint components."""

    def __init__(self, blueprint: HypernovaBlueprint) -> None:
        self.blueprint = blueprint

    # ------------------------------------------------------------------
    # Beat generation primitives
    # ------------------------------------------------------------------

    def _pulse_beats(self) -> Iterable[SagaBeat]:
        for stream in self.blueprint.pulse_streams:
            nodes = self._pulse_nodes(stream)
            synopsis = self._render_pulse_synopsis(stream, nodes)
            yield SagaBeat(
                title=f"Pulse Orbit {stream.stream_id}",
                synopsis=synopsis,
                involved_nodes=nodes,
                resonance=stream.glyph_signature.aggregate_intensity(),
                glyph_trace=stream.glyph_signature.describe(),
            )

    def _stratum_beats(self) -> Iterable[SagaBeat]:
        for stratum in self.blueprint.strata:
            nodes = list(stratum.nodes)
            synopsis = self._render_stratum_synopsis(stratum)
            glyph_trace = stratum.harmonic_signature.describe()
            yield SagaBeat(
                title=f"Stratum {stratum.name}",
                synopsis=synopsis,
                involved_nodes=nodes,
                resonance=stratum.harmonic_signature.aggregate_intensity(),
                glyph_trace=glyph_trace,
            )

    def _domain_beats(self) -> Iterable[SagaBeat]:
        for domain in self.blueprint.domains:
            centroid = domain.centroid()
            synopsis = textwrap.fill(
                (
                    f"Domain {domain.name} orbits around centroid {centroid!r} while "
                    f"{len(domain.nodes)} nodes synchronize {len(domain.conduits)} conduits."
                ),
                width=92,
            )
            glyph_trace = ", ".join(node.glyph.symbol for node in domain.nodes)
            yield SagaBeat(
                title=f"Domain {domain.name}",
                synopsis=synopsis,
                involved_nodes=[node.node_id for node in domain.nodes],
                resonance=domain.resonance_score(),
                glyph_trace=glyph_trace,
            )

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------

    def _pulse_nodes(self, stream: HyperpulseStream) -> List[str]:
        nodes: List[str] = []
        for conduit in stream.conduits:
            if conduit.source not in nodes:
                nodes.append(conduit.source)
            if conduit.target not in nodes:
                nodes.append(conduit.target)
        return nodes

    def _render_pulse_synopsis(self, stream: HyperpulseStream, nodes: Sequence[str]) -> str:
        cadence = stream.cadence_bpm
        path = stream.described_path()
        synopsis = (
            f"Hyperpulse {stream.stream_id} ripples across {len(nodes)} nodes at {cadence} BPM, "
            f"tracing {path or 'no defined path'}."
        )
        return textwrap.fill(synopsis, width=90)

    def _render_stratum_synopsis(self, stratum: MythicStratum) -> str:
        density = stratum.density()
        synopsis = (
            f"Mythic layer {stratum.name} enfolds nodes {', '.join(stratum.nodes)} and resonates "
            f"with density {density:.2f}."
        )
        return textwrap.fill(synopsis, width=90)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_saga(self) -> List[SagaBeat]:
        beats = list(itertools.chain(self._domain_beats(), self._stratum_beats(), self._pulse_beats()))
        beats.sort(key=lambda beat: beat.resonance, reverse=True)
        return beats

    def render_text(self) -> str:
        beats = self.build_saga()
        sections = [beat.to_text() for beat in beats]
        intro = textwrap.dedent(
            """
            # Hypernova Saga Chronicle

            The saga interprets architectural data as sweeping mythic arcs,
            preserving the sense of scale embedded in the blueprint.
            """
        ).strip()
        return intro + "\n\n" + "\n\n".join(sections)

    def chronicle_topics(self) -> List[str]:
        return sorted(self.blueprint.chronicle.entries)


__all__ = ["HypernovaSagaBuilder", "SagaBeat"]
