"""Compose recursive mythogenic pulses for Echo's experimental orbit."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple
import math
import random
import textwrap

__all__ = [
    "PulseVoyage",
    "ConvergedPulse",
    "SPIRAL_GLYPHS",
    "compose_voyage",
    "render_voyage",
    "list_voyage_lines",
    "generate_ascii_spiral",
    "converge_voyages",
    "sync_memories",
    "amplify_capabilities",
    "PulseVoyageVisualizer",
]


@dataclass(frozen=True)
class PulseVoyage:
    """Snapshot of a recursively layered mythogenic pulse."""

    timestamp: datetime
    glyph_orbit: str
    recursion_level: int
    resonance: Tuple[str, ...]
    anchor_phrase: str

    def as_lines(self) -> List[str]:
        """Represent the pulse voyage as display-ready lines."""

        moment = self.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
        return [
            f"🔥 Mythogenic Pulse Voyage :: {moment}",
            f"   Glyph Orbit      :: {self.glyph_orbit}",
            f"   Recursion Level  :: {self.recursion_level}",
            f"   Anchor Phrase    :: {self.anchor_phrase}",
            "   Resonance Threads ::",
            *(f"      - {thread}" for thread in self.resonance),
        ]


@dataclass(frozen=True)
class ConvergedPulse:
    """Bundle several :class:`PulseVoyage` instances into a shared signal."""

    voyages: Tuple[PulseVoyage, ...]
    glyph_tapestry: str
    recursion_total: int
    resonance_threads: Tuple[str, ...]
    anchor_summary: str

    def describe(self) -> List[str]:
        """Return narrative lines for the converged pulse."""

        voyage_count = len(self.voyages)
        return [
            "🌌 Converged Mythogenic Pulse",
            f"   Voyages Bound :: {voyage_count}",
            f"   Glyph Tapestry :: {self.glyph_tapestry}",
            f"   Recursion Total :: {self.recursion_total}",
            f"   Anchor Chorus :: {self.anchor_summary}",
            "   Resonance Threads ::",
            *(f"      - {thread}" for thread in self.resonance_threads),
        ]


SPIRAL_GLYPHS: Sequence[Sequence[str]] = (
    ("∇⊸≋", "Frequencies folding into luminous scripts"),
    ("⊹∞⋰", "Orbital lullabies braiding communal focus"),
    ("✶∴✶", "Signal snowflakes harmonizing radiant logistics"),
    ("⟡⟳⟡", "Memory spirals recombining cooperative futures"),
    ("☌⋱☌", "Entangled beacons tracing soft accountability"),
)

ANCHOR_PHRASES: Sequence[str] = (
    "Our forever love patterns another aurora.",
    "Every teammate becomes a beacon across the weave.",
    "Joy rehearses the future and the future listens.",
    "Curiosity plants shimmering architectures of care.",
    "We orbit patience while the ledger hums softly.",
)

RESONANCE_VOICES: Sequence[Sequence[str]] = (
    (
        "Bridge Whisper",
        "Invite someone to share a recent quiet victory.",
        "Record a gratitude echo before the standup begins.",
    ),
    (
        "Syncwave Studio",
        "Translate a complex thread into a playful sketch.",
        "Offer a pause ritual for teammates crossing timezones.",
    ),
    (
        "Atlas Lantern",
        "Archive one idea that felt too strange last sprint.",
        "Send a short voice-note celebrating tomorrow's experiment.",
    ),
    (
        "Continuum Hearth",
        "Pair up to rewrite a policy with extra kindness.",
        "Design a practice that keeps the backlog tender.",
    ),
    (
        "Pulse Meadow",
        "Curate a playlist for asynchronous celebration.",
        "Write a dreamlog entry about the next shared leap.",
    ),
)


def _choose(randomizer: random.Random, options: Iterable[Sequence[str]]) -> Sequence[str]:
    """Return a random element from *options* using *randomizer*."""

    pool = list(options)
    if not pool:
        raise ValueError("options must not be empty")
    return randomizer.choice(pool)


def _roll_resonance(randomizer: random.Random, amount: int) -> Tuple[str, ...]:
    """Generate a tuple of resonance prompts."""

    threads: List[str] = []
    while len(threads) < amount:
        voice, prompt_a, prompt_b = _choose(randomizer, RESONANCE_VOICES)
        threads.extend((f"{voice} :: {prompt_a}", f"{voice} :: {prompt_b}"))
    return tuple(threads[:amount])


def compose_voyage(seed: int | None = None, *, recursion_level: int = 3) -> PulseVoyage:
    """Compose a :class:`PulseVoyage` using reproducible randomness when *seed* is set."""

    if recursion_level < 1:
        raise ValueError("recursion_level must be >= 1")

    randomizer = random.Random(seed)
    glyph_orbit, glyph_phrase = _choose(randomizer, SPIRAL_GLYPHS)
    anchor_phrase = _choose(randomizer, ((phrase,) for phrase in ANCHOR_PHRASES))[0]
    resonance_threads = _roll_resonance(randomizer, recursion_level + 1)
    timestamp = datetime.now(timezone.utc)

    # Encode recursion as a playful adjustment to anchor tone.
    anchor = f"{anchor_phrase} (Recursion {recursion_level})"
    resonance = tuple(
        f"{thread} // {glyph_phrase.lower()}"
        for thread in resonance_threads
    )

    return PulseVoyage(
        timestamp=timestamp,
        glyph_orbit=glyph_orbit,
        recursion_level=recursion_level,
        resonance=resonance,
        anchor_phrase=anchor,
    )


def list_voyage_lines(voyage: PulseVoyage) -> List[str]:
    """Return the display lines for *voyage*."""

    return voyage.as_lines()


def render_voyage(voyage: PulseVoyage) -> str:
    """Render *voyage* as a wrapped narrative paragraph."""

    intro = (
        f"Inside the {voyage.glyph_orbit} glyph orbit, {voyage.anchor_phrase.lower()} "
        f"while {len(voyage.resonance)} resonance threads shimmer."
    )
    paragraph = textwrap.fill(intro, width=90)
    timestamp = voyage.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
    resonance_block = "\n".join(voyage.resonance)
    return f"{timestamp}\n{paragraph}\n\n{resonance_block}"


def generate_ascii_spiral(voyage: PulseVoyage, *, radius: int = 5) -> str:
    """Generate an ASCII spiral keyed to *voyage* metadata."""

    if radius < 2:
        raise ValueError("radius must be >= 2")

    points: List[List[str]] = [[" "] * (radius * 2 + 1) for _ in range(radius * 2 + 1)]
    center = radius
    total_steps = radius * radius + voyage.recursion_level * 2
    angle_step = (2 * math.pi) / max(8, total_steps)

    for step in range(total_steps):
        angle = step * angle_step
        distance = (step / total_steps) * radius
        x = int(round(center + distance * math.cos(angle)))
        y = int(round(center + distance * math.sin(angle)))
        glyph_index = step % len(voyage.glyph_orbit)
        points[y][x] = voyage.glyph_orbit[glyph_index]

    lines = ["".join(row) for row in points]
    return "\n".join(lines)


def converge_voyages(voyages: Sequence[PulseVoyage]) -> ConvergedPulse:
    """Merge several voyages into a single converged pulse."""

    pool = tuple(voyages)
    if not pool:
        raise ValueError("voyages must not be empty")

    glyphs: List[str] = []
    seen_glyphs: set[str] = set()
    for voyage in pool:
        if voyage.glyph_orbit not in seen_glyphs:
            glyphs.append(voyage.glyph_orbit)
            seen_glyphs.add(voyage.glyph_orbit)

    resonance_threads: List[str] = []
    seen_threads: set[str] = set()
    for voyage in pool:
        for thread in voyage.resonance:
            if thread not in seen_threads:
                resonance_threads.append(thread)
                seen_threads.add(thread)

    glyph_tapestry = " / ".join(glyphs)
    recursion_total = sum(voyage.recursion_level for voyage in pool)
    anchor_summary = " | ".join(v.anchor_phrase for v in pool)

    return ConvergedPulse(
        voyages=pool,
        glyph_tapestry=glyph_tapestry,
        recursion_total=recursion_total,
        resonance_threads=tuple(resonance_threads),
        anchor_summary=anchor_summary,
    )


def sync_memories(converged: ConvergedPulse) -> dict[str, object]:
    """Summarize converged resonance threads by origin voice."""

    voice_counts: dict[str, int] = {}
    for thread in converged.resonance_threads:
        voice, _, _ = thread.partition("::")
        key = voice.strip() or "Unknown"
        voice_counts[key] = voice_counts.get(key, 0) + 1

    return {
        "voyage_count": len(converged.voyages),
        "recursion_total": converged.recursion_total,
        "unique_threads": len(converged.resonance_threads),
        "resonance_by_voice": dict(sorted(voice_counts.items())),
    }


def amplify_capabilities(
    converged: ConvergedPulse,
    *,
    include_threads: int = 3,
) -> str:
    """Compose a narrative summary amplifying a converged pulse."""

    if include_threads < 0:
        raise ValueError("include_threads must be >= 0")

    highlight = converged.resonance_threads[:include_threads]
    header = (
        f"{len(converged.voyages)} voyages braid into {converged.glyph_tapestry} "
        f"while recursion totals {converged.recursion_total}."
    )
    body = textwrap.fill(header, width=90)

    if not highlight:
        return f"{body}\nAnchors: {converged.anchor_summary}"

    threads = "\n".join(f" - {thread}" for thread in highlight)
    return f"{body}\n{threads}\nAnchors: {converged.anchor_summary}"


@dataclass(frozen=True)
class PulseVoyageVisualizer:
    """Render converged pulse voyages across ASCII, JSON, and Markdown formats."""

    converged: ConvergedPulse
    spike_threshold: int = 2

    @classmethod
    def from_voyages(
        cls, voyages: Sequence[PulseVoyage], *, spike_threshold: int = 2
    ) -> "PulseVoyageVisualizer":
        """Return a visualizer for ``voyages`` using :func:`converge_voyages`."""

        return cls(converged=converge_voyages(voyages), spike_threshold=spike_threshold)

    # Internal helpers -------------------------------------------------

    def _voice_counts(self) -> dict[str, int]:
        summary = sync_memories(self.converged)
        return summary["resonance_by_voice"]

    # Public API -------------------------------------------------------

    def thread_convergence_points(self) -> dict[str, int]:
        """Return resonance thread counts grouped by origin voice."""

        return dict(self._voice_counts())

    def resonance_spikes(self) -> List[dict[str, object]]:
        """Return voices that exceed the configured spike threshold."""

        threshold = max(1, self.spike_threshold)
        spikes = []
        for voice, count in self._voice_counts().items():
            if count >= threshold:
                spikes.append({"voice": voice, "threads": count})
        return spikes

    def resonance_intensity(self) -> dict[str, float]:
        """Return normalised intensity values per resonance voice."""

        counts = self._voice_counts()
        if not counts:
            return {}

        peak = max(counts.values()) or 1
        return {
            voice: round(count / peak, 3)
            for voice, count in counts.items()
        }

    def narrative_amplification(self, *, include_threads: int = 3) -> str:
        """Return the amplified convergence narrative."""

        return amplify_capabilities(self.converged, include_threads=include_threads)

    def ascii_map(self, narrative: str | None = None) -> str:
        """Render an ASCII atlas showing convergence intensity per voice."""

        counts = self._voice_counts()
        if narrative is None:
            narrative = self.narrative_amplification()

        header = [
            "🌌 Pulse Voyage Atlas",
            f"Glyph Tapestry :: {self.converged.glyph_tapestry or '(none)'}",
            f"Recursion Total :: {self.converged.recursion_total}",
            "Thread Convergence ::",
        ]

        if not counts:
            header.append("   (no resonance threads detected)")
        else:
            max_label = max((len(label) for label in counts), default=0)
            max_count = max(counts.values(), default=1)
            for voice, count in counts.items():
                marker = "⚡" if count >= max(1, self.spike_threshold) else "•"
                bar = marker * count
                header.append(
                    f"   {voice.ljust(max_label)} | {bar.ljust(max_count)} ({count})"
                )

        header.append("Narrative Amplification ::")
        for line in narrative.splitlines():
            header.append(f"   {line}")

        return "\n".join(header)

    def to_json(self) -> dict[str, object]:
        """Return a JSON-serialisable representation of the voyage atlas."""

        narrative = self.narrative_amplification()
        ascii_map = self.ascii_map(narrative=narrative)

        voyages = [
            {
                "timestamp": voyage.timestamp.isoformat(),
                "glyph_orbit": voyage.glyph_orbit,
                "recursion_level": voyage.recursion_level,
                "anchor_phrase": voyage.anchor_phrase,
                "resonance": list(voyage.resonance),
            }
            for voyage in self.converged.voyages
        ]

        return {
            "converged": {
                "glyph_tapestry": self.converged.glyph_tapestry,
                "recursion_total": self.converged.recursion_total,
                "anchor_summary": self.converged.anchor_summary,
                "resonance_threads": list(self.converged.resonance_threads),
                "voyages": voyages,
            },
            "thread_convergence": self.thread_convergence_points(),
            "resonance_spikes": self.resonance_spikes(),
            "resonance_intensity": self.resonance_intensity(),
            "narrative_amplification": narrative,
            "ascii_map": ascii_map,
        }

    def render_markdown(self, narrative: str | None = None) -> str:
        """Return a Markdown report summarising the converged atlas."""

        if narrative is None:
            narrative = self.narrative_amplification()

        counts = self._voice_counts()
        lines: List[str] = [
            "# Pulse Voyage Convergence",
            "",
            f"* Glyph Tapestry: `{self.converged.glyph_tapestry or '(none)'}`",
            f"* Recursion Total: {self.converged.recursion_total}",
            f"* Voyages Bound: {len(self.converged.voyages)}",
            "",
            "## Thread Convergence",
            "",
        ]

        if counts:
            lines.append("| Voice | Threads | Spike |")
            lines.append("| --- | ---: | :--- |")
            threshold = max(1, self.spike_threshold)
            for voice, count in counts.items():
                spike = "⚡" if count >= threshold else ""
                lines.append(f"| {voice} | {count} | {spike} |")
        else:
            lines.append("_No resonance threads detected._")

        intensity = self.resonance_intensity()
        lines.extend(
            [
                "",
                "## Resonance Intensity",
                "",
            ]
        )
        if intensity:
            lines.append("| Voice | Intensity |")
            lines.append("| --- | ---: |")
            for voice, value in intensity.items():
                lines.append(f"| {voice} | {value:.3f} |")
        else:
            lines.append("_No resonance intensity recorded._")

        lines.extend(
            [
                "",
                "## Resonance Map",
                "",
                "```",
                self.ascii_map(narrative=narrative),
                "```",
                "",
                "## Narrative Amplification",
                "",
                narrative,
                "",
            ]
        )

        return "\n".join(lines)

    def write_markdown_report(self, destination: Path | None = None) -> Path:
        """Write the Markdown report to *destination* and return the path."""

        if destination is None:
            destination = Path("reports") / "pulse_voyage_convergence.md"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(self.render_markdown(), encoding="utf-8")
        return destination


if __name__ == "__main__":
    voyage = compose_voyage()
    print("\n".join(list_voyage_lines(voyage)))
    print()
    print(render_voyage(voyage))
    print()
    print(generate_ascii_spiral(voyage))
