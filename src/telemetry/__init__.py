"""Ethical telemetry primitives with privacy-first defaults."""

from .schema import ConsentState, TelemetryContext, TelemetryEvent
from .collector import PendingTelemetryEvent, TelemetryCollector
from .storage import InMemoryTelemetryStorage, JsonlTelemetryStorage, TelemetryStorage
from .report import (
    VitalityReport,
    VitalityReportError,
    generate_vitality_report,
    main as generate_vitality_report_cli,
)

__all__ = [
    "ConsentState",
    "TelemetryContext",
    "TelemetryEvent",
    "PendingTelemetryEvent",
    "TelemetryCollector",
    "TelemetryStorage",
    "InMemoryTelemetryStorage",
    "JsonlTelemetryStorage",
    "VitalityReport",
    "VitalityReportError",
    "generate_vitality_report",
    "generate_vitality_report_cli",
]
