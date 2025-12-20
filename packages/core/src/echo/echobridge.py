"""EchoBridge integration layer between NeuralLink and OuterLink."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence

from outerlink.runtime import OuterLinkRuntime

from .neural_link import NeuralLinkPulse, NeuralLinkSystem

__all__ = [
    "EchoBridgePacket",
    "EchoBridge",
]


@dataclass(slots=True, frozen=True)
class EchoBridgePacket:
    """Portable bridge payload containing both neural and outerlink context."""

    created_at: str
    outerlink_state: Mapping[str, Any]
    neural_pulse: NeuralLinkPulse
    bridge_event: Optional[Mapping[str, Any]]
    compatibility: Mapping[str, Any]


class EchoBridge:
    """Synchronize NeuralLink pulses with OuterLink runtime events."""

    def __init__(
        self,
        neural_link: NeuralLinkSystem,
        outerlink_runtime: Optional[OuterLinkRuntime] = None,
    ) -> None:
        self.neural_link = neural_link
        self.outerlink_runtime = outerlink_runtime
        self._history: list[EchoBridgePacket] = []

    def bridge(
        self,
        *,
        outerlink_state: Optional[Mapping[str, Any]] = None,
        source: str = "outerlink",
    ) -> EchoBridgePacket:
        if outerlink_state is None:
            if not self.outerlink_runtime:
                raise ValueError("outerlink_state is required when no OuterLink runtime is provided")
            outerlink_state = self.outerlink_runtime.emit_state()

        pulse = self.neural_link.pulse_from_outerlink(outerlink_state, source=source)
        bridge_event = None
        if self.outerlink_runtime:
            bridge_event = self.outerlink_runtime.ingest_neural_link(pulse.to_outerlink_payload())

        compatibility = {
            "outerlink_online": bool(outerlink_state.get("online")),
            "outerlink_digest": outerlink_state.get("digest"),
            "neural_signal": pulse.prediction.signal,
            "neural_confidence": pulse.prediction.confidence,
        }

        packet = EchoBridgePacket(
            created_at=datetime.now(timezone.utc).isoformat(),
            outerlink_state=outerlink_state,
            neural_pulse=pulse,
            bridge_event=bridge_event,
            compatibility=compatibility,
        )
        self._history.append(packet)
        return packet

    def history(self) -> Sequence[EchoBridgePacket]:
        return tuple(self._history)
