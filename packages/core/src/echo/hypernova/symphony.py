"""Musical metaphor utilities for :mod:`echo.hypernova`."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Mapping, Sequence, Tuple

from .architecture import ContinuumDomain, HypernovaBlueprint, HyperpulseStream, MythicStratum


@dataclass(slots=True)
class NovaInstrument:
    """Instrument descriptor for hypernova performances."""

    name: str
    waveform: str
    octave_range: Tuple[int, int]
    motif: Tuple[int, ...]

    def describe(self) -> str:
        low, high = self.octave_range
        motif = "-".join(str(step) for step in self.motif)
        return f"{self.name} [{self.waveform}] {low}-{high} :: {motif}"


@dataclass(slots=True)
class ScoreFragment:
    """Composable fragment derived from blueprint components."""

    title: str
    tempo: int
    measures: List[List[int]]
    instrument: NovaInstrument

    def signature(self) -> str:
        return f"{self.title} @ {self.tempo} BPM using {self.instrument.describe()}"

    def flatten(self) -> List[int]:
        notes: List[int] = []
        for measure in self.measures:
            notes.extend(measure)
        return notes


class HypernovaSymphony:
    """Generate score fragments from the blueprint for sonic experiences."""

    def __init__(self, blueprint: HypernovaBlueprint) -> None:
        self.blueprint = blueprint
        self.instruments = self._derive_instruments()

    # ------------------------------------------------------------------
    # Instrument derivation
    # ------------------------------------------------------------------

    def _derive_instruments(self) -> List[NovaInstrument]:
        palette = [
            ("Aurora Synth", "sine", (2, 5), (2, 5, 7, 9)),
            ("Pulse Drums", "percussive", (1, 2), (1, 1, 2, 1)),
            ("Echo Strings", "saw", (3, 6), (3, 4, 5, 4)),
            ("Quantum Bells", "triangle", (4, 7), (5, 7, 9, 12)),
        ]
        instruments = [
            NovaInstrument(name=name, waveform=waveform, octave_range=octaves, motif=motif)
            for name, waveform, octaves, motif in palette
        ]
        return instruments

    # ------------------------------------------------------------------
    # Fragment creation
    # ------------------------------------------------------------------

    def _tempo_from_stream(self, stream: HyperpulseStream) -> int:
        base = stream.cadence_bpm
        return base + int(stream.coherence * 12)

    def _notes_from_domain(self, domain: ContinuumDomain) -> List[int]:
        notes = []
        for node in domain.nodes:
            base = int(sum(abs(coord) for coord in node.coordinates) % 12)
            notes.append(48 + base)
        return notes

    def _notes_from_stratum(self, stratum: MythicStratum) -> List[int]:
        density = stratum.density()
        base_note = 60 + int((density % 6) * 2)
        return [base_note + idx for idx in range(len(stratum.nodes))]

    def _select_instrument(self, index: int) -> NovaInstrument:
        return self.instruments[index % len(self.instruments)]

    def _measures_from_notes(self, notes: Sequence[int], measure_length: int = 4) -> List[List[int]]:
        measures: List[List[int]] = []
        for index in range(0, len(notes), measure_length):
            measures.append(list(notes[index : index + measure_length]))
        if measures and len(measures[-1]) < measure_length:
            last = measures[-1]
            last.extend([last[-1]] * (measure_length - len(last)))
        return measures

    def build_fragments(self) -> List[ScoreFragment]:
        fragments: List[ScoreFragment] = []
        for idx, stream in enumerate(self.blueprint.pulse_streams):
            tempo = self._tempo_from_stream(stream)
            notes = self._notes_from_domain(self.blueprint.domains[idx % len(self.blueprint.domains)])
            measures = self._measures_from_notes(notes)
            instrument = self._select_instrument(idx)
            fragments.append(
                ScoreFragment(
                    title=f"Pulse {stream.stream_id}",
                    tempo=tempo,
                    measures=measures,
                    instrument=instrument,
                )
            )
        for idx, stratum in enumerate(self.blueprint.strata):
            notes = self._notes_from_stratum(stratum)
            measures = self._measures_from_notes(notes)
            instrument = self._select_instrument(idx + len(self.blueprint.pulse_streams))
            fragments.append(
                ScoreFragment(
                    title=f"Stratum {stratum.name}",
                    tempo=88 + idx * 6,
                    measures=measures,
                    instrument=instrument,
                )
            )
        return fragments

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render_score(self) -> str:
        fragments = self.build_fragments()
        lines = ["# Hypernova Symphony", ""]
        for fragment in fragments:
            lines.append(f"## {fragment.title}")
            lines.append(fragment.signature())
            flattened = " ".join(str(note) for note in fragment.flatten())
            lines.append(f"Notes: {flattened}")
            lines.append("")
        return "\n".join(lines).strip()

    def to_midi_instructions(self) -> Mapping[str, object]:
        fragments = self.build_fragments()
        return {
            "tempo_map": {fragment.title: fragment.tempo for fragment in fragments},
            "instrument_map": {fragment.title: fragment.instrument.describe() for fragment in fragments},
            "note_sequences": {fragment.title: fragment.flatten() for fragment in fragments},
        }


__all__ = ["HypernovaSymphony", "NovaInstrument", "ScoreFragment"]
