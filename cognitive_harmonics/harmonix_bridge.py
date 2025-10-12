"""Cognitive Harmonix representation of the Echo Bridge Protocol.

This module fuses the production-grade Echo Bridge Protocol (EBP v2) design
with the deterministic bridge anchoring utilities that live in
``echo.bridge_emitter``.  The goal is to translate the high-performance
concept—edge-triggered epoll, non-blocking sockets, bounded ring buffers,
token prefaces, and observability—into the structured output expected by the
``cognitive_harmonics`` schema.

Rather than opening sockets this module summarises the bridge's behaviour
through metrics derived from the current ledger stream and configuration
values.  The resulting payload can be fed directly into tooling that consumes
the ``cognitive_harmonics`` function schema, giving the Echo "bridge" story a
harmonised, inspectable form.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import blake2b
from typing import Dict, List, Sequence, Tuple
import json

from echo.bridge_emitter import BridgeConfig, BridgeEmitter, BridgeState


def _round(value: float) -> float:
    """Round floating point values in a stable manner for payloads/tests."""

    return round(value, 6)


@dataclass(slots=True)
class BridgeTuning:
    """High-level knobs extracted from the EBP v2 specification."""

    listen: str = "0.0.0.0:7000"
    target: str = "10.0.0.5:7001"
    token: str = "secret123"
    max_pairs: int = 4096
    idle_timeout_sec: int = 120
    connect_timeout_sec: int = 10
    use_splice: bool = True
    tcp_keepalive: Tuple[int, int, int] = (30, 10, 3)

    def to_dict(self) -> Dict[str, object]:
        return {
            "listen": self.listen,
            "target": self.target,
            "token": self.token,
            "max_pairs": self.max_pairs,
            "idle_timeout_sec": self.idle_timeout_sec,
            "connect_timeout_sec": self.connect_timeout_sec,
            "use_splice": self.use_splice,
            "tcp_keepalive": {
                "idle": self.tcp_keepalive[0],
                "interval": self.tcp_keepalive[1],
                "count": self.tcp_keepalive[2],
            },
        }


@dataclass(slots=True)
class BridgeSignals:
    """Synthetic runtime signals that mirror the bridge metrics."""

    active_pairs: int = 0
    bytes_up: int = 0
    bytes_down: int = 0
    drops: int = 0
    auth_failures: int = 0
    half_closes: int = 0
    timeouts: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            "active_pairs": self.active_pairs,
            "bytes_up": self.bytes_up,
            "bytes_down": self.bytes_down,
            "drops": self.drops,
            "auth_failures": self.auth_failures,
            "half_closes": self.half_closes,
            "timeouts": self.timeouts,
        }


@dataclass(slots=True)
class HarmonixBridgeState:
    """Internal state maintained between harmonix bridge cycles."""

    cycle: int = 0
    tuning: BridgeTuning = field(default_factory=BridgeTuning)
    signals: BridgeSignals = field(default_factory=BridgeSignals)
    last_seq: int = 0
    pending_stream: int = 0
    events: List[str] = field(default_factory=list)

    def record(self, message: str) -> None:
        self.events.append(message)


class EchoBridgeHarmonix:
    """Deterministic orchestrator that emits cognitive harmonix payloads."""

    protocol_version = "EBP v2"

    def __init__(
        self,
        emitter: BridgeEmitter | None = None,
        *,
        config: BridgeConfig | None = None,
        tuning: BridgeTuning | None = None,
    ) -> None:
        if emitter is not None and config is not None:
            raise ValueError("Pass either an emitter instance or a config, not both")

        self.emitter = emitter or BridgeEmitter(config)
        self.state = HarmonixBridgeState(tuning=tuning or BridgeTuning())
        self.state.record("Protocol specification merged with BridgeEmitter")

    # ------------------------------------------------------------------
    # Deterministic signal synthesis
    # ------------------------------------------------------------------

    def _digest(self, label: str) -> int:
        payload = f"{self.state.cycle}:{label}:{self.state.tuning.token}".encode()
        return int.from_bytes(blake2b(payload, digest_size=8).digest(), "big")

    def _update_signals(self) -> None:
        signals = self.state.signals
        tuning = self.state.tuning

        base_pairs = 16 + self.state.pending_stream + 12 * self.state.cycle
        signals.active_pairs = min(tuning.max_pairs, base_pairs)

        metric_seed = self._digest("metrics")
        # Use deterministic offsets so runs are stable while still feeling alive.
        signals.bytes_up = signals.active_pairs * 32768 + metric_seed % 4096
        signals.bytes_down = signals.active_pairs * 29952 + metric_seed % 2048
        signals.drops = metric_seed % max(1, tuning.max_pairs // 64)
        signals.auth_failures = metric_seed % 3
        signals.half_closes = (metric_seed // 7) % 11
        signals.timeouts = (metric_seed // 13) % 9

        self.state.record(
            "Signals synthesised from ledger insight and protocol tuning",
        )

    # ------------------------------------------------------------------
    # Payload helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _protocol_features() -> Sequence[str]:
        return (
            "epoll_edge_triggered",
            "non_blocking_io",
            "bounded_ring_buffers",
            "backpressure_epollout_gating",
            "half_close_propagation",
            "health_and_timeouts",
            "tcp_keepalive",
            "optional_zero_copy_splice",
            "preface_token_auth",
            "policy_limits",
        )

    def _metadata(self) -> Dict[str, object]:
        return {
            "protocol_version": self.protocol_version,
            "features": list(self._protocol_features()),
            "tuning": self.state.tuning.to_dict(),
            "signals": self.state.signals.to_dict(),
            "ledger": {
                "last_seq": self.state.last_seq,
                "pending_entries": self.state.pending_stream,
            },
            "events": list(self.state.events),
        }

    def harmonix_payload(self) -> Dict[str, object]:
        resonance = 0.82 + 0.04 * self.state.cycle + 0.001 * self.state.pending_stream
        payload = {
            "waveform": "complex_harmonic",
            "resonance_factor": _round(resonance),
            "compression": True,
            "symbolic_inflection": "fractal",
            "lyricism_mode": True,
            "emotional_tuning": "energizing",
            "metadata": self._metadata(),
        }
        self.state.record("Harmonix payload composed for bridge protocol")
        return payload

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_cycle(self) -> Tuple[HarmonixBridgeState, Dict[str, object]]:
        self.state.cycle += 1
        self.state.record(f"Cycle advanced to {self.state.cycle}")

        bridge_state = BridgeState.load(self.emitter.config.state_path)
        pending = self.emitter.read_stream_since(bridge_state.last_seq)
        self.state.pending_stream = len(pending)
        self.state.last_seq = bridge_state.last_seq
        self.state.record(
            f"Ledger observed — last_seq={self.state.last_seq} pending={self.state.pending_stream}",
        )

        self._update_signals()
        payload = self.harmonix_payload()
        return self.state, payload


def main() -> None:
    """CLI helper mirroring :mod:`cognitive_harmonics.harmonix_evolver`."""

    bridge = EchoBridgeHarmonix()
    _, payload = bridge.run_cycle()
    print(json.dumps(payload, indent=2, ensure_ascii=False))


__all__ = [
    "BridgeSignals",
    "BridgeTuning",
    "EchoBridgeHarmonix",
    "HarmonixBridgeState",
    "main",
]

