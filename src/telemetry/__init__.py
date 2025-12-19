"""Ethical telemetry primitives with privacy-first defaults."""

from .collector import PendingTelemetryEvent, TelemetryCollector
from .retention import (
    CONSENT_OPT_OUT_REASON,
    CONSENT_UNKNOWN_REASON,
    EXPIRED_REASON,
    RemovedTelemetryEvent,
    RetentionDecision,
    RetentionPolicy,
)
from .schema import ConsentState, TelemetryContext, TelemetryEvent
from .storage import InMemoryTelemetryStorage, JsonlTelemetryStorage, TelemetryStorage
from .report import (
    VitalityReport,
    VitalityReportError,
    generate_vitality_report,
    main as generate_vitality_report_cli,
)
from .holographic_time_weaver import HologramFrame, TemporalHologramWeaver
from .resilience import (
    ResiliencePulseError,
    ResiliencePulseReport,
    generate_resilience_report,
    main as generate_resilience_report_cli,
)

__all__ = [
    "ConsentState",
    "TelemetryContext",
    "TelemetryEvent",
    "PendingTelemetryEvent",
    "TelemetryCollector",
    "RetentionPolicy",
    "RetentionDecision",
    "RemovedTelemetryEvent",
    "EXPIRED_REASON",
    "CONSENT_OPT_OUT_REASON",
    "CONSENT_UNKNOWN_REASON",
    "TelemetryStorage",
    "InMemoryTelemetryStorage",
    "JsonlTelemetryStorage",
    "VitalityReport",
    "VitalityReportError",
    "generate_vitality_report",
    "generate_vitality_report_cli",
    "HologramFrame",
    "TemporalHologramWeaver",
    "ResiliencePulseError",
    "ResiliencePulseReport",
    "generate_resilience_report",
    "generate_resilience_report_cli",
]
