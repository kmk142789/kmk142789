"""Cognitive Echo Bridge (CEB).

This module coordinates narrative signals across channels and produces
bridge-ready diagnostics that emphasise shared language.  The bridge is
implemented as a light-weight, deterministic data structure so it can be
used in documentation examples, notebooks, and tests without external
systems.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from typing import Mapping, Sequence


@dataclass(frozen=True)
class BridgeEdge:
    """Resonance edge between two channels."""

    source: str
    target: str
    resonance: float
    shared_terms: tuple[str, ...]


@dataclass(frozen=True)
class CognitiveEchoBridgeReport:
    """High-level summary of the bridge state."""

    identity: str
    coherence: float
    edges: tuple[BridgeEdge, ...]
    dominant_topics: tuple[str, ...]


def _tokenize(message: str) -> set[str]:
    """Return a normalised token set for the supplied message."""

    cleaned = message.replace("/", " ")
    tokens: set[str] = set()

    for raw_token in cleaned.split():
        token = raw_token.strip(".,;:!?\"'()[]{}<>|\\`).").lower()
        if token:
            tokens.add(token)

    return tokens


class CognitiveEchoBridge:
    """Construct resonance-aware bridges across narrative channels."""

    def __init__(self, *, smoothing: float = 0.1, min_shared: int = 1) -> None:
        self.smoothing = max(0.0, smoothing)
        self.min_shared = max(0, min_shared)

    def build_bridge(
        self, identity: str, signals: Mapping[str, Sequence[str]]
    ) -> CognitiveEchoBridgeReport:
        """Return a deterministic bridge report for the provided signals."""

        normalised = {
            channel: _tokenize(" ".join(messages)) for channel, messages in signals.items()
        }

        edges: list[BridgeEdge] = []
        for (source, source_tokens), (target, target_tokens) in combinations(
            normalised.items(), 2
        ):
            shared = sorted(source_tokens & target_tokens)
            if len(shared) < self.min_shared:
                continue

            union = source_tokens | target_tokens
            resonance = (len(shared) + self.smoothing) / (len(union) + self.smoothing)
            edge = BridgeEdge(
                source=source,
                target=target,
                resonance=round(resonance, 3),
                shared_terms=tuple(shared),
            )
            edges.append(edge)

        edges.sort(key=lambda edge: (-edge.resonance, edge.source, edge.target))
        coherence = round(
            sum(edge.resonance for edge in edges) / len(edges), 3
        ) if edges else 0.0

        topic_counter: Counter[str] = Counter()
        for token_set in normalised.values():
            topic_counter.update(token_set)
        dominant_topics = tuple(topic for topic, _ in topic_counter.most_common(5))

        return CognitiveEchoBridgeReport(
            identity=identity,
            coherence=coherence,
            edges=tuple(edges),
            dominant_topics=dominant_topics,
        )
