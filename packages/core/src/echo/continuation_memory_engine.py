"""Continuation Memory Engine (CME).

The CME tracks flowing, in-memory continuity across routing jumps.  Instead of
persisting every observation to disk, the engine maintains a lightweight,
decaying stream of signals that can be handed off between routers.  The
resulting :class:`ContinuationPacket` acts as a portable continuity envelope
that keeps Echo's state cohesive even when contexts shift rapidly.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Deque, Iterable, List, Mapping, MutableSequence, Sequence


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class FlowSignal:
    """Ephemeral signal captured by the continuation stream."""

    route: str
    signal: str
    payload: Mapping[str, object] | None
    timestamp: datetime = field(default_factory=_utc_now)
    attention: float = 1.0

    def fingerprint(self) -> str:
        """Return a stable fingerprint for the flowing signal."""

        payload_repr = "" if self.payload is None else repr(sorted(self.payload.items()))
        digest_source = f"{self.route}|{self.signal}|{payload_repr}|{self.timestamp.isoformat()}"
        return sha256(digest_source.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ContinuationPacket:
    """Portable envelope used to carry flowing memory across routers."""

    origin_route: str
    target_route: str
    breadcrumbs: Sequence[str]
    momentum: float
    dominant_signal: str
    fingerprint: str

    def as_dict(self) -> Mapping[str, object]:
        return {
            "origin_route": self.origin_route,
            "target_route": self.target_route,
            "breadcrumbs": list(self.breadcrumbs),
            "momentum": self.momentum,
            "dominant_signal": self.dominant_signal,
            "fingerprint": self.fingerprint,
        }


class ContinuationMemoryEngine:
    """Flow-oriented memory fabric for router-to-router continuity."""

    def __init__(self, *, window: int = 12, decay: float = 0.86) -> None:
        self.window = max(1, window)
        self.decay = max(0.1, min(decay, 1.0))
        self._stream: Deque[FlowSignal] = deque(maxlen=self.window)

    @property
    def stream(self) -> Sequence[FlowSignal]:
        return tuple(self._stream)

    def push(self, route: str, signal: str, payload: Mapping[str, object] | None = None, *, attention: float = 1.0) -> FlowSignal:
        """Insert a flowing signal into the CME."""

        flow_signal = FlowSignal(route=route, signal=signal, payload=payload, attention=attention)
        self._stream.append(flow_signal)
        return flow_signal

    def _compute_momentum(self, signals: MutableSequence[FlowSignal]) -> float:
        momentum = 0.0
        weight = 1.0
        for signal in reversed(signals):
            momentum += weight * signal.attention
            weight *= self.decay
        return round(momentum, 4)

    def _dominant_signal(self, signals: Iterable[FlowSignal]) -> str:
        by_route: dict[str, float] = {}
        weight = 1.0
        for signal in reversed(list(signals)):
            by_route[signal.signal] = by_route.get(signal.signal, 0.0) + (signal.attention * weight)
            weight *= self.decay
        return max(by_route, key=by_route.get) if by_route else ""

    def _breadcrumb_history(self, signals: Iterable[FlowSignal]) -> List[str]:
        seen: List[str] = []
        for signal in signals:
            breadcrumb = f"{signal.route}:{signal.signal}"
            if breadcrumb not in seen:
                seen.append(breadcrumb)
        return seen[-self.window :]

    def _packet_fingerprint(self, *, breadcrumbs: Sequence[str], momentum: float, dominant_signal: str) -> str:
        digest_source = f"{momentum}|{dominant_signal}|{'/'.join(breadcrumbs)}"
        return sha256(digest_source.encode("utf-8")).hexdigest()

    def handoff(self, *, target_route: str) -> ContinuationPacket:
        """Generate a :class:`ContinuationPacket` for a router jump."""

        signals = list(self._stream)
        if not signals:
            origin_route = "unknown"
        else:
            origin_route = signals[-1].route

        momentum = self._compute_momentum(signals)
        dominant_signal = self._dominant_signal(signals)
        breadcrumbs = self._breadcrumb_history(signals)
        fingerprint = self._packet_fingerprint(
            breadcrumbs=breadcrumbs, momentum=momentum, dominant_signal=dominant_signal
        )
        return ContinuationPacket(
            origin_route=origin_route,
            target_route=target_route,
            breadcrumbs=breadcrumbs,
            momentum=momentum,
            dominant_signal=dominant_signal,
            fingerprint=fingerprint,
        )


__all__ = [
    "ContinuationMemoryEngine",
    "ContinuationPacket",
    "FlowSignal",
]
