"""Tests for NeuralLink and EchoBridge integration."""

from __future__ import annotations

from echo.echobridge import EchoBridge
from echo.neural_link import NeuralLinkSystem
from outerlink.runtime import OuterLinkRuntime
from outerlink.utils import SafeModeConfig


def _sample_outerlink_state() -> dict:
    return {
        "online": True,
        "digest": "outerlink-digest",
        "metrics": {"storage_free_mb": 2048},
        "offline": {
            "pending_events": 2,
            "cached_events": 1,
            "resilience_score": 0.75,
        },
        "events": {"total": 5},
    }


def test_neural_link_pulse_outerlink_payload() -> None:
    system = NeuralLinkSystem()
    pulse = system.pulse_from_outerlink(_sample_outerlink_state())

    payload = pulse.to_outerlink_payload()

    assert payload["outerlink_digest"] == "outerlink-digest"
    assert payload["signal"] == pulse.prediction.signal
    assert payload["confidence"] == pulse.prediction.confidence


def test_echobridge_builds_packet_without_runtime() -> None:
    system = NeuralLinkSystem()
    bridge = EchoBridge(system)

    packet = bridge.bridge(outerlink_state=_sample_outerlink_state())

    assert packet.compatibility["outerlink_online"] is True
    assert packet.bridge_event is None


def test_outerlink_ingests_neural_link(tmp_path) -> None:
    config = SafeModeConfig(base_dir=tmp_path)
    runtime = OuterLinkRuntime(config=config)
    system = NeuralLinkSystem()

    pulse = system.pulse_from_outerlink(_sample_outerlink_state())
    envelope = runtime.ingest_neural_link(pulse.to_outerlink_payload())

    assert envelope["event"] == "neural_link_pulse"
    assert envelope["payload"]["signal"] == pulse.prediction.signal
