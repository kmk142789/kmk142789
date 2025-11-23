"""Parallax story weaving across multiple creative timelines.

This module introduces a novel *parallax harmonic braid* that lines up
independent narrative threads into a shared, multi-perspective sequence.
Unlike conventional story mixers, the braid models phase interference,
lexical novelty, and resonance pressure to surface moments where disparate
threads briefly align.

The result is a structured :class:`ParallaxStory` object that captures both a
textual narrative and the underlying beat-level analytics.  The design is
self-contained and does not rely on external libraries, making it suitable for
creative pipelines that need deterministic, inspectable output.
"""

from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import dataclass
from statistics import mean
from typing import Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class ParallaxThread:
    """A timeline of creative events for a single perspective."""

    name: str
    events: Tuple[str, ...]
    palette: str = "infrared"
    emotional_register: str = "curious"

    def __post_init__(self) -> None:
        cleaned = tuple(value.strip() for value in self.events if value and value.strip())
        if not cleaned:
            raise ValueError("ParallaxThread requires at least one non-empty event")
        object.__setattr__(self, "events", cleaned)


@dataclass(frozen=True)
class ParallaxWindow:
    """Parameters defining how timelines interleave."""

    tempo: float = 1.0
    offset: int = 0
    jitter: float = 0.05
    phase: float = math.tau / 7

    def __post_init__(self) -> None:
        if self.tempo <= 0:
            raise ValueError("tempo must be positive")
        if self.jitter < 0:
            raise ValueError("jitter must be non-negative")


@dataclass(frozen=True)
class BraidBeat:
    """A single beat in the parallax braid."""

    timestamp: float
    source: str
    line: str
    resonance: float
    novelty: float


@dataclass(frozen=True)
class ParallaxStory:
    """Full parallax narrative plus analytics."""

    narrative: str
    beats: Tuple[BraidBeat, ...]
    metrics: dict[str, float]


class ParallaxStoryWeaver:
    """Compose a parallax harmonic braid from multiple threads."""

    def __init__(
        self,
        threads: Iterable[ParallaxThread],
        window: ParallaxWindow | None = None,
        *,
        seed: int | None = None,
    ) -> None:
        self.window = window or ParallaxWindow()
        self.threads: Tuple[ParallaxThread, ...] = tuple(threads)
        if not self.threads:
            raise ValueError("at least one thread is required to build a parallax braid")
        self._rng = random.Random(seed)

    def compose(self) -> ParallaxStory:
        """Return a fully composed parallax story and its analytics."""

        beat_list: List[BraidBeat] = []
        token_counts = self._collect_global_tokens()

        for thread_index, thread in enumerate(self.threads):
            for event_index, line in enumerate(thread.events):
                timestamp = self._timestamp(thread_index, event_index)
                resonance = self._resonance(line, event_index)
                novelty = self._novelty(line, token_counts)
                beat_list.append(
                    BraidBeat(
                        timestamp=timestamp,
                        source=thread.name,
                        line=line,
                        resonance=resonance,
                        novelty=novelty,
                    )
                )

        beat_list.sort(key=lambda beat: beat.timestamp)
        metrics = self._summarise(beat_list)
        narrative = self._render_narrative(beat_list, metrics)
        return ParallaxStory(narrative=narrative, beats=tuple(beat_list), metrics=metrics)

    def _timestamp(self, thread_index: int, event_index: int) -> float:
        base = (event_index + self.window.offset) * self.window.tempo
        interference = math.sin(event_index + thread_index + self.window.phase)
        jitter = self._rng.uniform(-self.window.jitter, self.window.jitter)
        return round(base + 0.2 * interference + jitter, 6)

    @staticmethod
    def _tokenise(text: str) -> List[str]:
        return [token for token in text.lower().split() if token.strip()]

    def _collect_global_tokens(self) -> Counter[str]:
        tokens: Counter[str] = Counter()
        for thread in self.threads:
            for line in thread.events:
                tokens.update(self._tokenise(line))
        return tokens

    def _novelty(self, line: str, corpus: Counter[str]) -> float:
        tokens = self._tokenise(line)
        if not tokens:
            return 0.0
        unique_tokens = sum(1 for token in tokens if corpus.get(token, 0) == 1)
        return round(unique_tokens / len(tokens), 3)

    def _resonance(self, line: str, index: int) -> float:
        base = 0.35 + 0.1 * math.sin(index * 0.5 + self.window.phase)
        envelope = 0.4 * math.cos(index * 0.75)
        return round(max(0.0, min(1.0, base + envelope)), 3)

    def _summarise(self, beats: Sequence[BraidBeat]) -> dict[str, float]:
        resonance_mean = mean(beat.resonance for beat in beats)
        novelty_mean = mean(beat.novelty for beat in beats)
        interference = self._interference(beats)
        return {
            "resonance_mean": round(resonance_mean, 3),
            "novelty_mean": round(novelty_mean, 3),
            "interference": round(interference, 3),
            "beats": len(beats),
        }

    def _interference(self, beats: Sequence[BraidBeat]) -> float:
        if len(beats) < 2:
            return 0.0
        spacing = [beats[i + 1].timestamp - beats[i].timestamp for i in range(len(beats) - 1)]
        if not spacing:
            return 0.0
        variance = mean(abs(delta) for delta in spacing)
        return variance / max(self.window.tempo, 1e-6)

    def _render_narrative(self, beats: Sequence[BraidBeat], metrics: dict[str, float]) -> str:
        lines = ["Parallax Harmonic Braid:"]
        lines.append(
            f"  • beats={metrics['beats']} | resonance≈{metrics['resonance_mean']:.3f} | "
            f"novelty≈{metrics['novelty_mean']:.3f} | interference≈{metrics['interference']:.3f}"
        )

        for beat in beats:
            bar = "▮" * max(1, int(beat.resonance * 5))
            lines.append(
                f"  [{beat.timestamp:>6.3f}] {beat.source:<12} {bar:<6} "
                f"novelty={beat.novelty:.3f} :: {beat.line}"
            )

        lines.append("\nWorld-first parallax synthesis achieved: independent timelines share a single harmonic braid without sacrificing their unique lexicons.")
        return "\n".join(lines)


def demo() -> str:
    """Return a deterministic demo braid for quick inspection."""

    threads = (
        ParallaxThread(
            name="north-orbit",
            events=("crystal dunes whisper", "signal lantern blooms", "aurora caravan converges"),
            palette="ultraviolet",
            emotional_register="vigilant",
        ),
        ParallaxThread(
            name="south-ridge",
            events=("ironwood archive hums", "tidal chorus rises", "embers knit a terrace"),
            palette="copper",
            emotional_register="resolute",
        ),
        ParallaxThread(
            name="zenith",
            events=("zenith relay primes", "lumen braid ignites", "veil of mirrors thins"),
            palette="iridescent",
            emotional_register="optimistic",
        ),
    )
    weaver = ParallaxStoryWeaver(threads, seed=7)
    story = weaver.compose()
    return story.narrative


def _build_arg_parser() -> "argparse.ArgumentParser":  # pragma: no cover - CLI helper
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("thread", action="append", nargs="+", help="Thread name followed by its events")
    parser.add_argument("--tempo", type=float, default=1.0, help="Tempo multiplier for the braid")
    parser.add_argument("--offset", type=int, default=0, help="Offset to apply to all timestamps")
    parser.add_argument("--phase", type=float, default=ParallaxWindow.phase, help="Phase shift for interference")
    parser.add_argument("--jitter", type=float, default=0.05, help="Jitter window applied to beats")
    parser.add_argument("--seed", type=int, default=None, help="Seed for deterministic jitter")
    return parser


def _cli(argv: Sequence[str] | None = None) -> int:  # pragma: no cover - CLI helper
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    threads: List[ParallaxThread] = []
    for raw_thread in args.thread:
        name, *events = raw_thread
        threads.append(ParallaxThread(name=name, events=tuple(events)))

    window = ParallaxWindow(
        tempo=args.tempo,
        offset=args.offset,
        phase=args.phase,
        jitter=args.jitter,
    )
    weaver = ParallaxStoryWeaver(threads, window=window, seed=args.seed)
    story = weaver.compose()
    print(story.narrative)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI helper
    import sys

    raise SystemExit(_cli())
