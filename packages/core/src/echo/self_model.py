"""Composable self-model that fuses observation, memory, and intent."""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Callable, Deque, Iterable, Mapping, MutableMapping, Sequence

from .memory.analytics import MemoryAnalytics
from .memory.store import ExecutionContext, JsonMemoryStore
from .semantic_negotiation import NegotiationIntent

if TYPE_CHECKING:
    from .privacy.zk_layer import ProofResult, ZeroKnowledgePrivacyLayer


# ---------------------------------------------------------------------------
# Observer subsystem
# ---------------------------------------------------------------------------


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class ObserverEvent:
    """Structured event captured by :class:`ObserverSubsystem`."""

    timestamp: datetime
    kind: str
    data: MutableMapping[str, object]


@dataclass(slots=True)
class ObserverSnapshot:
    """Aggregated view of recent observations."""

    total_events: int
    window_events: int
    kind_counts: Mapping[str, int]
    latest_event: Mapping[str, object] | None
    rate_per_minute: float
    signal: float


class ObserverSubsystem:
    """Capture and score runtime observations for downstream consumers."""

    def __init__(
        self,
        *,
        window_seconds: int = 300,
        max_events: int = 2048,
        target_rate_per_minute: float = 30.0,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self._window_seconds = window_seconds
        self._target_rate = max(1.0, target_rate_per_minute)
        self._clock = clock
        self._events: Deque[ObserverEvent] = deque(maxlen=max_events)

    def record(self, kind: str, data: Mapping[str, object] | None = None) -> ObserverEvent:
        """Record an observation and return the captured event."""

        payload = ObserverEvent(
            timestamp=self._clock(),
            kind=kind,
            data=dict(data or {}),
        )
        self._events.append(payload)
        return payload

    def snapshot(self) -> ObserverSnapshot:
        """Return a scored snapshot of the current observation buffer."""

        self._prune_window()
        total = len(self._events)
        if total == 0:
            return ObserverSnapshot(
                total_events=0,
                window_events=0,
                kind_counts={},
                latest_event=None,
                rate_per_minute=0.0,
                signal=0.0,
            )

        kind_counts = Counter(event.kind for event in self._events)
        window_events = self._count_window_events()
        rate_per_minute = window_events / max(1.0, self._window_seconds / 60.0)
        signal = min(1.0, round(rate_per_minute / self._target_rate, 4))
        latest = self._events[-1]
        latest_payload = {
            "timestamp": latest.timestamp.isoformat(),
            "kind": latest.kind,
            "data": dict(latest.data),
        }
        return ObserverSnapshot(
            total_events=total,
            window_events=window_events,
            kind_counts=dict(kind_counts),
            latest_event=latest_payload,
            rate_per_minute=round(rate_per_minute, 4),
            signal=signal,
        )

    def _prune_window(self) -> None:
        cutoff = self._clock().timestamp() - self._window_seconds
        while self._events and self._events[0].timestamp.timestamp() < cutoff:
            self._events.popleft()

    def _count_window_events(self) -> int:
        if not self._events:
            return 0
        cutoff = self._clock().timestamp() - self._window_seconds
        return sum(1 for event in self._events if event.timestamp.timestamp() >= cutoff)


# ---------------------------------------------------------------------------
# Memory unifier
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class MemorySnapshot:
    """Unified view over recent execution memory."""

    command_frequency: Mapping[str, int]
    metadata_summary: Mapping[str, list[Mapping[str, object]]]
    timeline: Sequence[Mapping[str, object]]
    coverage: float


class MemoryUnifier:
    """Fuse historical execution contexts into a compact summary."""

    def __init__(self, executions: Sequence[ExecutionContext] | None = None) -> None:
        self._executions = list(executions or [])
        self._analytics = MemoryAnalytics(self._executions)

    @classmethod
    def from_store(
        cls,
        store: JsonMemoryStore,
        *,
        limit: int | None = None,
        metadata_filter: Mapping[str, object] | None = None,
    ) -> "MemoryUnifier":
        executions = store.recent_executions(limit=limit, metadata_filter=metadata_filter)
        return cls(executions)

    def unify(
        self,
        *,
        metadata_keys: Sequence[str] = ("cycle", "intent", "phase"),
        recent_limit: int = 10,
    ) -> MemorySnapshot:
        """Return a consolidated view over the stored execution contexts."""

        command_frequency = self._analytics.command_frequency()
        metadata_summary: dict[str, list[Mapping[str, object]]] = {}
        for key in metadata_keys:
            counts = self._analytics.metadata_value_counts(key)
            if counts:
                metadata_summary[key] = [
                    {"value": entry.value, "count": entry.count}
                    for entry in counts
                ]

        timeline = self._analytics.timeline()[:recent_limit]
        coverage = self._coverage_ratio()
        return MemorySnapshot(
            command_frequency=command_frequency,
            metadata_summary=metadata_summary,
            timeline=timeline,
            coverage=coverage,
        )

    def _coverage_ratio(self) -> float:
        if not self._executions:
            return 0.0
        with_summary = sum(1 for ctx in self._executions if ctx.summary)
        return round(with_summary / len(self._executions), 4)


# ---------------------------------------------------------------------------
# Intent resolver
# ---------------------------------------------------------------------------


def _tokenize(text: str | None) -> set[str]:
    if not text:
        return set()
    tokens = {token.lower() for token in text.replace("/", " ").split()}
    return {token.strip(".,:;!?()[]{}") for token in tokens if token}


def _priority_weight(priority: str | None) -> float:
    if not priority:
        return 0.5
    normalized = priority.lower()
    if normalized in {"urgent", "critical", "p0", "high"}:
        return 1.0
    if normalized in {"medium", "p1"}:
        return 0.75
    if normalized in {"low", "p2"}:
        return 0.4
    return 0.5


@dataclass(slots=True)
class IntentResolution:
    """Resolution details produced by :class:`IntentResolver`."""

    intent: NegotiationIntent | None
    confidence: float
    rationale: str
    candidates: list[Mapping[str, object]] = field(default_factory=list)


class IntentResolver:
    """Score intents against natural language prompts and metadata."""

    def __init__(self, intents: Iterable[NegotiationIntent] | None = None) -> None:
        self._intents = list(intents or [])

    def register(self, intent: NegotiationIntent) -> None:
        self._intents.append(intent)

    def resolve(
        self,
        query: str | None,
        *,
        tags: Sequence[str] | None = None,
        desired_outcome: str | None = None,
    ) -> IntentResolution:
        if not self._intents:
            return IntentResolution(intent=None, confidence=0.0, rationale="no intents registered")

        query_tokens = _tokenize(query)
        query_tokens.update(_tokenize(" ".join(tags)) if tags else set())
        desired_tokens = _tokenize(desired_outcome)

        scored: list[tuple[NegotiationIntent, float, str]] = []
        for intent in self._intents:
            score, reason = self._score_intent(intent, query_tokens, desired_tokens)
            scored.append((intent, score, reason))

        best = max(scored, key=lambda item: item[1])
        candidates = [
            {
                "topic": intent.topic,
                "score": round(score, 4),
                "reason": reason,
            }
            for intent, score, reason in scored
        ]
        rationale = best[2]
        return IntentResolution(
            intent=best[0],
            confidence=round(best[1], 4),
            rationale=rationale,
            candidates=candidates,
        )

    def _score_intent(
        self,
        intent: NegotiationIntent,
        query_tokens: set[str],
        desired_tokens: set[str],
    ) -> tuple[float, str]:
        tokens = _tokenize(intent.topic)
        tokens.update(_tokenize(intent.summary))
        for tag in intent.tags:
            tokens.update(_tokenize(tag))
        overlap = len(query_tokens & tokens)
        score = 0.0
        reason_parts: list[str] = []
        if query_tokens:
            score += min(0.6, overlap / max(len(query_tokens), 1))
            if overlap:
                reason_parts.append(f"matched {overlap} query terms")
        if desired_tokens and intent.desired_outcome:
            intent_tokens = _tokenize(intent.desired_outcome)
            desired_overlap = len(desired_tokens & intent_tokens)
            if desired_overlap:
                score += 0.25
                reason_parts.append("desired outcome aligns")
        score += 0.15 * _priority_weight(intent.priority)
        reason = ", ".join(reason_parts) if reason_parts else "baseline priority"
        return min(1.0, score), reason


# ---------------------------------------------------------------------------
# Self-model
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class SelfModelSnapshot:
    """Composite reflection emitted by :class:`SelfModel`."""

    generated_at: str
    observer: ObserverSnapshot
    memory: MemorySnapshot
    intent: IntentResolution
    diagnostics: Mapping[str, object]


class SelfModel:
    """High-level fusion of observer, memory, and intent systems."""

    def __init__(
        self,
        observer: ObserverSubsystem,
        memory_unifier: MemoryUnifier,
        intent_resolver: IntentResolver,
        *,
        clock: Callable[[], datetime] = _utc_now,
        privacy_layer: "ZeroKnowledgePrivacyLayer" | None = None,
    ) -> None:
        self._observer = observer
        self._memory = memory_unifier
        self._intent = intent_resolver
        self._clock = clock
        self._privacy_layer = privacy_layer
        self._proof_cache: list["ProofResult"] = []

    @property
    def observer(self) -> ObserverSubsystem:
        return self._observer

    @property
    def memory(self) -> MemoryUnifier:
        return self._memory

    @property
    def intents(self) -> IntentResolver:
        return self._intent

    def reflect(
        self,
        *,
        query: str | None = None,
        tags: Sequence[str] | None = None,
        desired_outcome: str | None = None,
    ) -> SelfModelSnapshot:
        observer_snapshot = self._observer.snapshot()
        memory_snapshot = self._memory.unify()
        intent_resolution = self._intent.resolve(
            query,
            tags=tags,
            desired_outcome=desired_outcome,
        )
        diagnostics = {
            "observer_signal": observer_snapshot.signal,
            "memory_coverage": memory_snapshot.coverage,
            "intent_confidence": intent_resolution.confidence,
        }
        if self._privacy_layer:
            proofs = self._privacy_layer.recent_proofs(limit=5)
            self._proof_cache = proofs
            diagnostics["privacy_signal"] = self._privacy_layer.privacy_signal()
            diagnostics["privacy_commitments"] = [result.commitment for result in proofs]
        else:
            self._proof_cache = []
        return SelfModelSnapshot(
            generated_at=self._clock().isoformat(),
            observer=observer_snapshot,
            memory=memory_snapshot,
            intent=intent_resolution,
            diagnostics=diagnostics,
        )

    def latest_proofs(self) -> list["ProofResult"]:
        """Return the internally cached proofs (full view)."""

        return list(self._proof_cache)


__all__ = [
    "ObserverSubsystem",
    "ObserverSnapshot",
    "ObserverEvent",
    "MemoryUnifier",
    "MemorySnapshot",
    "IntentResolver",
    "IntentResolution",
    "SelfModel",
    "SelfModelSnapshot",
]
