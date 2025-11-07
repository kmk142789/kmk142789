"""Ethical telemetry primitives with privacy-first defaults."""

from .schema import ConsentState, TelemetryContext, TelemetryEvent
from .collector import TelemetryCollector
from .storage import InMemoryTelemetryStorage, JsonlTelemetryStorage, TelemetryStorage

__all__ = [
    "ConsentState",
    "TelemetryContext",
    "TelemetryEvent",
    "TelemetryCollector",
    "TelemetryStorage",
    "InMemoryTelemetryStorage",
    "JsonlTelemetryStorage",
]
